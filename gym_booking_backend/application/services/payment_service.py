from datetime import timedelta
from uuid import uuid4
from django.utils import timezone

from gym_booking_backend.domain.constants import BookingStatus, InvoiceItemType, InvoiceStatus, PaymentMethod, PaymentStatus
from gym_booking_backend.domain.exceptions import GymException
from gym_booking_backend.infrastructure.repositories.membership_repository import membership_repository
from gym_booking_backend.infrastructure.repositories.payment_repository import payment_repository
from gym_booking_backend.infrastructure.repositories.invoice_repository import invoice_repository
from gym_booking_backend.infrastructure.repositories.booking_repository import booking_repository
from gym_booking_backend.application.interfaces.services.ipayment_service import IPaymentService
from gym_booking_backend.domain.result import Result


def _generate_transaction_code():
    return f"TXN{timezone.now():%Y%m%d}{uuid4().hex[:10].upper()}"


class PaymentService(IPaymentService):
    def create_payment(self, user, membership_id, payment_method) -> Result:
        try:
            membership = membership_repository.get_user_membership_by_id(user, membership_id)
            if not membership:
                return Result.failure_result("Membership not found.", status_code=404)

            invoice_item = invoice_repository.get_invoice_item_by_membership(membership.id)

            invoice = invoice_item.invoice if invoice_item else None
            if not invoice:
                invoice_number = f"INV-{timezone.now():%Y%m%d}-{uuid4().hex[:6].upper()}"
                invoice = invoice_repository.create_invoice(
                    user=user,
                    invoice_number=invoice_number,
                    total_amount=membership.package.price,
                    status=InvoiceStatus.UNPAID
                )
                invoice_repository.create_invoice_item(
                    invoice=invoice,
                    item_type=InvoiceItemType.MEMBERSHIP,
                    object_id=membership.id,
                    amount=membership.package.price
                )

            payment = payment_repository.create_payment(
                user=user,
                membership=membership,
                amount=membership.package.price,
                payment_method=payment_method,
                transaction_code=_generate_transaction_code(),
                invoice=invoice,
            )
            return Result.success_result(payment, status_code=201)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def confirm_payment(self, payment_id) -> Result:
        try:
            payment = payment_repository.get_payment_by_id(payment_id)
            if not payment:
                return Result.failure_result("Payment not found.", status_code=404)
            payment.status = PaymentStatus.SUCCESS
            payment.paid_at = timezone.now()
            payment.save(update_fields=["status", "paid_at"])

            if payment.invoice:
                invoice = payment.invoice
                invoice.status = InvoiceStatus.PAID
                invoice.save(update_fields=["status", "updated_at"])

            if payment.membership:
                from gym_booking_backend.domain.constants import MembershipStatus
                if payment.membership.status == MembershipStatus.PENDING:
                    membership = payment.membership
                    membership.status = MembershipStatus.ACTIVE
                    if not membership.start_date:
                        membership.start_date = timezone.localdate()
                    membership.end_date = membership.start_date + timedelta(days=membership.package.duration_days)
                    membership.save(update_fields=["status", "start_date", "end_date", "updated_at"])

            if payment.invoice:
                from gym_booking_backend.infrastructure.models import InvoiceItem
                booking_item = InvoiceItem.objects.filter(
                    invoice=payment.invoice,
                    item_type=InvoiceItemType.CLASS_FEE
                ).first()
                if booking_item and booking_item.object_id:
                    trainer_booking = booking_repository.get_trainer_booking_by_id(booking_item.object_id)
                    if trainer_booking and trainer_booking.status == BookingStatus.PENDING:
                        trainer_booking.status = BookingStatus.CONFIRMED
                        trainer_booking.save(update_fields=["status", "updated_at"])

            return Result.success_result(payment, status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def fail_payment(self, payment_id) -> Result:
        try:
            payment = payment_repository.get_payment_by_id(payment_id)
            if not payment:
                return Result.failure_result("Payment not found.", status_code=404)
            payment.status = PaymentStatus.FAILED
            payment.save(update_fields=["status"])
            return Result.success_result(payment, status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def refund_payment(self, payment_id) -> Result:
        try:
            payment = payment_repository.get_payment_by_id(payment_id)
            if not payment:
                return Result.failure_result("Payment not found.", status_code=404)
            payment.status = PaymentStatus.REFUNDED
            payment.save(update_fields=["status"])
            return Result.success_result(payment, status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def get_my_payments(self, user) -> Result:
        payments = payment_repository.get_user_payments(user)
        return Result.success_result(payments, status_code=200)

    def create_trainer_booking_payment(self, user, trainer_booking_id, payment_method) -> Result:
        try:
            if payment_method not in {choice[0] for choice in PaymentMethod.choices}:
                return Result.failure_result("Invalid payment method.", status_code=400)

            booking = booking_repository.get_trainer_booking_by_id(trainer_booking_id)
            if not booking or booking.user_id != user.id:
                return Result.failure_result("Trainer booking not found.", status_code=404)

            if booking.status == "cancelled":
                return Result.failure_result("Cannot pay for a cancelled trainer booking.", status_code=400)

            invoice_item = invoice_repository.get_invoice_item_by_class_fee(booking.id)

            if invoice_item:
                invoice = invoice_item.invoice
            else:
                amount = booking.trainer.session_price
                invoice_number = f"INV-{timezone.now():%Y%m%d}-{uuid4().hex[:6].upper()}"
                invoice = invoice_repository.create_invoice(
                    user=user,
                    invoice_number=invoice_number,
                    total_amount=amount,
                    status=InvoiceStatus.UNPAID,
                )
                invoice_repository.create_invoice_item(
                    invoice=invoice,
                    item_type=InvoiceItemType.CLASS_FEE,
                    object_id=booking.id,
                    amount=amount,
                )

            if invoice.status == InvoiceStatus.PAID:
                return Result.failure_result("This trainer booking has already been paid.", status_code=400)

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
                return Result.success_result(existing_pending, status_code=200)

            payment = payment_repository.create_payment(
                user=user,
                membership=None,
                amount=invoice.total_amount,
                payment_method=payment_method,
                transaction_code=_generate_transaction_code(),
                invoice=invoice,
            )
            return Result.success_result(payment, status_code=201)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)


payment_service = PaymentService()
