from uuid import uuid4

from django.utils import timezone

from gym_booking_backend.domain.constants import BookingStatus, InvoiceItemType, InvoiceStatus, PaymentMethod, PaymentStatus
from gym_booking_backend.domain.exceptions import PaymentException
from gym_booking_backend.infrastructure.repositories import membership_repository, payment_repository


def _generate_transaction_code():
    return f"TXN{timezone.now():%Y%m%d}{uuid4().hex[:10].upper()}"


def create_payment(user, membership_id, payment_method):
    membership = membership_repository.get_user_membership_by_id(user, membership_id)
    if not membership:
        raise PaymentException("Membership not found.")

    from gym_booking_backend.infrastructure.models import Invoice, InvoiceItem, InvoiceItemType, InvoiceStatus
    # Look for an unpaid invoice associated with this membership
    invoice_item = InvoiceItem.objects.filter(
        item_type=InvoiceItemType.MEMBERSHIP,
        object_id=membership.id
    ).first()

    invoice = invoice_item.invoice if invoice_item else None
    if not invoice:
        # Fallback if no invoice was created
        invoice_number = f"INV-{timezone.now():%Y%m%d}-{uuid4().hex[:6].upper()}"
        invoice = Invoice.objects.create(
            user=user,
            invoice_number=invoice_number,
            total_amount=membership.package.price,
            status=InvoiceStatus.UNPAID
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            item_type=InvoiceItemType.MEMBERSHIP,
            object_id=membership.id,
            amount=membership.package.price
        )

    return payment_repository.create_payment(
        user=user,
        membership=membership,
        amount=membership.package.price,
        payment_method=payment_method,
        transaction_code=_generate_transaction_code(),
        invoice=invoice,
    )


def confirm_payment(payment_id):
    payment = payment_repository.get_payment_by_id(payment_id)
    if not payment:
        raise PaymentException("Payment not found.")
    payment.status = PaymentStatus.SUCCESS
    payment.paid_at = timezone.now()
    payment.save(update_fields=["status", "paid_at"])

    # Update associated Invoice status to Paid
    if payment.invoice:
        from gym_booking_backend.domain.constants import InvoiceStatus
        invoice = payment.invoice
        invoice.status = InvoiceStatus.PAID
        invoice.save(update_fields=["status", "updated_at"])

    # Update associated membership status to Active and set dates
    if payment.membership:
        from gym_booking_backend.domain.constants import MembershipStatus
        from datetime import timedelta
        membership = payment.membership
        membership.status = MembershipStatus.ACTIVE
        membership.start_date = timezone.localdate()
        membership.end_date = membership.start_date + timedelta(days=membership.package.duration_days)
        membership.save(update_fields=["status", "start_date", "end_date", "updated_at"])

    # Auto-confirm trainer 1-1 booking if this payment belongs to class_fee invoice item
    if payment.invoice:
        from gym_booking_backend.infrastructure.models import InvoiceItem, TrainerBooking

        booking_item = InvoiceItem.objects.filter(
            invoice=payment.invoice,
            item_type=InvoiceItemType.CLASS_FEE
        ).first()
        if booking_item and booking_item.object_id:
            trainer_booking = TrainerBooking.objects.filter(id=booking_item.object_id).first()
            if trainer_booking and trainer_booking.status == BookingStatus.PENDING:
                trainer_booking.status = BookingStatus.CONFIRMED
                trainer_booking.save(update_fields=["status", "updated_at"])

    return payment


def fail_payment(payment_id):
    payment = payment_repository.get_payment_by_id(payment_id)
    if not payment:
        raise PaymentException("Payment not found.")
    payment.status = PaymentStatus.FAILED
    payment.save(update_fields=["status"])
    return payment


def refund_payment(payment_id):
    payment = payment_repository.get_payment_by_id(payment_id)
    if not payment:
        raise PaymentException("Payment not found.")
    payment.status = PaymentStatus.REFUNDED
    payment.save(update_fields=["status"])
    return payment


def get_my_payments(user):
    return payment_repository.get_user_payments(user)


def create_trainer_booking_payment(user, trainer_booking_id, payment_method):
    from gym_booking_backend.infrastructure.models import Invoice, InvoiceItem, TrainerBooking

    if payment_method not in {choice[0] for choice in PaymentMethod.choices}:
        raise PaymentException("Invalid payment method.")

    booking = (
        TrainerBooking.objects.select_related("trainer")
        .filter(id=trainer_booking_id, user=user)
        .first()
    )
    if not booking:
        raise PaymentException("Trainer booking not found.")

    if booking.status == "cancelled":
        raise PaymentException("Cannot pay for a cancelled trainer booking.")

    invoice_item = (
        InvoiceItem.objects.select_related("invoice")
        .filter(item_type=InvoiceItemType.CLASS_FEE, object_id=booking.id)
        .first()
    )

    if invoice_item:
        invoice = invoice_item.invoice
    else:
        amount = booking.trainer.session_price
        invoice_number = f"INV-{timezone.now():%Y%m%d}-{uuid4().hex[:6].upper()}"
        invoice = Invoice.objects.create(
            user=user,
            invoice_number=invoice_number,
            total_amount=amount,
            status=InvoiceStatus.UNPAID,
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            item_type=InvoiceItemType.CLASS_FEE,
            object_id=booking.id,
            amount=amount,
        )

    if invoice.status == InvoiceStatus.PAID:
        raise PaymentException("This trainer booking has already been paid.")

    existing_pending = (
        payment_repository.get_user_payments(user)
        .filter(invoice=invoice, status=PaymentStatus.PENDING)
        .order_by("-created_at")
        .first()
    )
    if existing_pending:
        if existing_pending.payment_method != payment_method:
            existing_pending.payment_method = payment_method
            existing_pending.save(update_fields=["payment_method", "updated_at"])
        return existing_pending

    return payment_repository.create_payment(
        user=user,
        membership=None,
        amount=invoice.total_amount,
        payment_method=payment_method,
        transaction_code=_generate_transaction_code(),
        invoice=invoice,
    )
