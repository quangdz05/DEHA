from datetime import timedelta
from uuid import uuid4

from django.utils import timezone

from gym_booking_backend.domain.constants import (
    BookingStatus,
    InvoiceItemType,
    InvoiceStatus,
    MembershipStatus,
    PaymentMethod,
    PaymentStatus,
)
from gym_booking_backend.domain.exceptions import PaymentException
from gym_booking_backend.infrastructure.repositories import (
    booking_repository,
    invoice_repository,
    membership_repository,
    payment_repository,
)


class PaymentService:
    def __init__(self, payment_repo, membership_repo, invoice_repo, booking_repo):
        self.payment_repo = payment_repo
        self.membership_repo = membership_repo
        self.invoice_repo = invoice_repo
        self.booking_repo = booking_repo

    def _generate_transaction_code(self):
        return f"TXN{timezone.now():%Y%m%d}{uuid4().hex[:10].upper()}"

    def create_payment(self, user, membership_id, payment_method):
        membership = self.membership_repo.get_user_membership_by_id(user, membership_id)
        if not membership:
            raise PaymentException("Membership not found.")

        # Look for an unpaid invoice associated with this membership
        invoice_item = self.invoice_repo.get_invoice_item_by_membership(membership.id)

        invoice = invoice_item.invoice if invoice_item else None
        if not invoice:
            # Fallback if no invoice was created
            invoice_number = f"INV-{timezone.now():%Y%m%d}-{uuid4().hex[:6].upper()}"
            invoice = self.invoice_repo.create_invoice(
                user=user,
                invoice_number=invoice_number,
                total_amount=membership.package.price,
                status=InvoiceStatus.UNPAID,
            )
            self.invoice_repo.create_invoice_item(
                invoice=invoice,
                item_type=InvoiceItemType.MEMBERSHIP,
                object_id=membership.id,
                amount=membership.package.price,
            )

        return self.payment_repo.create_payment(
            user=user,
            membership=membership,
            amount=membership.package.price,
            payment_method=payment_method,
            transaction_code=self._generate_transaction_code(),
            invoice=invoice,
        )

    def confirm_payment(self, payment_id):
        payment = self.payment_repo.get_payment_by_id(payment_id)
        if not payment:
            raise PaymentException("Payment not found.")
        payment.status = PaymentStatus.SUCCESS
        payment.paid_at = timezone.now()
        payment.save(update_fields=["status", "paid_at"])

        # Update associated Invoice status to Paid
        if payment.invoice:
            invoice = payment.invoice
            invoice.status = InvoiceStatus.PAID
            invoice.save(update_fields=["status", "updated_at"])

        # Update associated membership status to Active and set dates
        if payment.membership:
            membership = payment.membership
            membership.status = MembershipStatus.ACTIVE
            membership.start_date = timezone.localdate()
            membership.end_date = membership.start_date + timedelta(days=membership.package.duration_days)
            membership.save(update_fields=["status", "start_date", "end_date", "updated_at"])

        # Auto-confirm trainer 1-1 booking if this payment belongs to class_fee invoice item
        if payment.invoice:
            booking_item = self.invoice_repo.get_invoice_item_by_class_fee(None)
            # Use invoice-level lookup for the specific invoice
            from gym_booking_backend.infrastructure.models import InvoiceItem, TrainerBooking

            booking_item = InvoiceItem.objects.filter(
                invoice=payment.invoice,
                item_type=InvoiceItemType.CLASS_FEE,
            ).first()
            if booking_item and booking_item.object_id:
                trainer_booking = self.booking_repo.get_trainer_booking_by_id(booking_item.object_id)
                if trainer_booking and trainer_booking.status == BookingStatus.PENDING:
                    trainer_booking.status = BookingStatus.CONFIRMED
                    trainer_booking.save(update_fields=["status", "updated_at"])

        return payment

    def fail_payment(self, payment_id):
        payment = self.payment_repo.get_payment_by_id(payment_id)
        if not payment:
            raise PaymentException("Payment not found.")
        payment.status = PaymentStatus.FAILED
        payment.save(update_fields=["status"])
        return payment

    def refund_payment(self, payment_id):
        payment = self.payment_repo.get_payment_by_id(payment_id)
        if not payment:
            raise PaymentException("Payment not found.")
        payment.status = PaymentStatus.REFUNDED
        payment.save(update_fields=["status"])
        return payment

    def get_my_payments(self, user):
        return self.payment_repo.get_user_payments(user)

    def create_trainer_booking_payment(self, user, trainer_booking_id, payment_method):
        if payment_method not in {choice[0] for choice in PaymentMethod.choices}:
            raise PaymentException("Invalid payment method.")

        booking = self.booking_repo.get_trainer_booking_by_id(trainer_booking_id)
        if not booking or booking.user_id != user.id:
            raise PaymentException("Trainer booking not found.")

        if booking.status == "cancelled":
            raise PaymentException("Cannot pay for a cancelled trainer booking.")

        invoice_item = self.invoice_repo.get_invoice_item_by_class_fee(booking.id)

        if invoice_item:
            invoice = invoice_item.invoice
        else:
            amount = booking.trainer.session_price
            invoice_number = f"INV-{timezone.now():%Y%m%d}-{uuid4().hex[:6].upper()}"
            invoice = self.invoice_repo.create_invoice(
                user=user,
                invoice_number=invoice_number,
                total_amount=amount,
                status=InvoiceStatus.UNPAID,
            )
            self.invoice_repo.create_invoice_item(
                invoice=invoice,
                item_type=InvoiceItemType.CLASS_FEE,
                object_id=booking.id,
                amount=amount,
            )

        if invoice.status == InvoiceStatus.PAID:
            raise PaymentException("This trainer booking has already been paid.")

        existing_pending = (
            self.payment_repo.get_user_payments(user)
            .filter(invoice=invoice, status=PaymentStatus.PENDING)
            .order_by("-created_at")
            .first()
        )
        if existing_pending:
            if existing_pending.payment_method != payment_method:
                existing_pending.payment_method = payment_method
                existing_pending.save(update_fields=["payment_method", "updated_at"])
            return existing_pending

        return self.payment_repo.create_payment(
            user=user,
            membership=None,
            amount=invoice.total_amount,
            payment_method=payment_method,
            transaction_code=self._generate_transaction_code(),
            invoice=invoice,
        )


# Backward compatibility instance and delegates
_service = PaymentService(payment_repository, membership_repository, invoice_repository, booking_repository)
create_payment = _service.create_payment
confirm_payment = _service.confirm_payment
fail_payment = _service.fail_payment
refund_payment = _service.refund_payment
get_my_payments = _service.get_my_payments
create_trainer_booking_payment = _service.create_trainer_booking_payment
