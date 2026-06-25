from datetime import timedelta
from django.db import transaction
from django.utils import timezone

from gym_booking_backend.application.validators import membership_validator
from gym_booking_backend.domain.constants import InvoiceItemType, InvoiceStatus, MembershipStatus, PaymentStatus, UserRole
from gym_booking_backend.domain.exceptions import GymException
from gym_booking_backend.infrastructure.repositories.membership_repository import membership_repository
from gym_booking_backend.infrastructure.repositories.invoice_repository import invoice_repository
from gym_booking_backend.application.interfaces.services.imembership_service import IMembershipService
from gym_booking_backend.domain.result import Result


class MembershipService(IMembershipService):
    @transaction.atomic
    def create_membership(self, user, package_id) -> Result:
        try:
            if not hasattr(user, "profile") or user.profile.role != UserRole.MEMBER:
                return Result.failure_result("Chỉ có hội viên mới được đăng ký gói tập.", status_code=400)

            package = membership_repository.get_package_by_id(package_id)
            if not package:
                return Result.failure_result("Membership package not found.", status_code=404)

            if membership_repository.has_active_or_pending_membership(user):
                return Result.failure_result("Bạn đã có gói tập đang hoạt động hoặc chờ thanh toán.", status_code=400)

            start_date = timezone.localdate()
            end_date = start_date + timedelta(days=package.duration_days)
            membership_validator.validate_membership_dates(start_date, end_date)
            
            membership = membership_repository.create_user_membership(user, package, start_date, end_date)

            from uuid import uuid4
            invoice_number = f"INV-{timezone.now():%Y%m%d}-{uuid4().hex[:6].upper()}"
            invoice = invoice_repository.create_invoice(
                user=user,
                invoice_number=invoice_number,
                total_amount=package.price,
                status=InvoiceStatus.UNPAID
            )
            invoice_repository.create_invoice_item(
                invoice=invoice,
                item_type=InvoiceItemType.MEMBERSHIP,
                object_id=membership.id,
                amount=package.price
            )

            return Result.success_result(membership, "Membership created successfully", status_code=201)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def cancel_membership(self, user, membership_id) -> Result:
        try:
            membership = membership_repository.get_user_membership_by_id(user, membership_id)
            if not membership:
                return Result.failure_result("Membership not found.", status_code=404)
            
            old_status = membership.status
            membership.status = MembershipStatus.CANCELLED
            membership.save(update_fields=["status"])

            if old_status == MembershipStatus.PENDING:
                invoice_item = invoice_repository.get_invoice_item_by_membership(membership.id)
                if invoice_item and invoice_item.invoice:
                    invoice = invoice_item.invoice
                    if invoice.status == InvoiceStatus.UNPAID:
                        invoice.status = InvoiceStatus.CANCELLED
                        invoice.save(update_fields=["status", "updated_at"])
                        
                        from gym_booking_backend.infrastructure.models import Payment
                        Payment.objects.filter(invoice=invoice, status=PaymentStatus.PENDING).update(status=PaymentStatus.FAILED)

            return Result.success_result(membership, "Membership cancelled", status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def expire_old_memberships(self) -> Result:
        today = timezone.localdate()
        expired_count = membership_repository.expire_memberships_before(today)
        return Result.success_result(expired_count, status_code=200)

    def get_my_memberships(self, user) -> Result:
        memberships = membership_repository.get_user_memberships(user)
        return Result.success_result(memberships, status_code=200)

    def get_active_packages(self) -> Result:
        packages = membership_repository.get_active_packages()
        return Result.success_result(packages, status_code=200)

    @transaction.atomic
    def freeze_membership(self, user, membership_id, start_date, end_date, reason="") -> Result:
        from datetime import datetime
        from gym_booking_backend.infrastructure.models import UserMembership, MembershipFreeze

        try:
            membership = UserMembership.objects.filter(id=membership_id, user=user).first()
            if not membership:
                return Result.failure_result("Membership not found.", status_code=404)
            if membership.status != MembershipStatus.ACTIVE:
                return Result.failure_result("Only active memberships can be frozen.", status_code=400)

            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

            if start_date >= end_date:
                return Result.failure_result("Start date must be before end date.", status_code=400)
            if start_date < timezone.localdate():
                return Result.failure_result("Freeze start date cannot be in the past.", status_code=400)

            duration_days = (end_date - start_date).days
            package = membership.package
            if not package.is_freezable:
                return Result.failure_result("This membership package is not freezable.", status_code=400)

            existing_freeze_days = sum(f.duration_days for f in membership.freezes.all())
            if existing_freeze_days + duration_days > package.max_freeze_days:
                return Result.failure_result(f"Freeze duration exceeds maximum allowed days ({package.max_freeze_days} days).", status_code=400)

            freeze = MembershipFreeze.objects.create(
                user_membership=membership,
                start_date=start_date,
                end_date=end_date,
                duration_days=duration_days,
                reason=reason
            )

            membership.end_date += timedelta(days=duration_days)
            membership.save(update_fields=["end_date"])
            return Result.success_result(freeze, "Membership frozen successfully", status_code=201)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)


membership_service = MembershipService()
