from datetime import timedelta
from django.db import transaction
from django.utils import timezone

from gym_booking_backend.application.validators import membership_validator
from gym_booking_backend.domain.constants import InvoiceItemType, InvoiceStatus, MembershipStatus, PaymentStatus, UserRole
from gym_booking_backend.domain.exceptions import GymException
from gym_booking_backend.infrastructure.repositories import invoice_repository, membership_repository, payment_repository


class MembershipService:
    def __init__(self, membership_repo, invoice_repo, payment_repo):
        self.membership_repo = membership_repo
        self.invoice_repo = invoice_repo
        self.payment_repo = payment_repo

    @transaction.atomic
    def create_membership(self, user, package_id):
        # Validate user is a member
        if not hasattr(user, "profile") or user.profile.role != UserRole.MEMBER:
            raise GymException("Chỉ có hội viên mới được đăng ký gói tập.")

        package = self.membership_repo.get_package_by_id(package_id)
        if not package:
            raise GymException("Membership package not found.")

        # Validate user has no active or pending membership
        if self.membership_repo.has_active_or_pending_membership(user):
            raise GymException("Bạn đã có gói tập đang hoạt động hoặc chờ thanh toán.")

        start_date = timezone.localdate()
        end_date = start_date + timedelta(days=package.duration_days)
        membership_validator.validate_membership_dates(start_date, end_date)

        membership = self.membership_repo.create_user_membership(user, package, start_date, end_date)

        # Automatically create Invoice and InvoiceItem
        from uuid import uuid4
        invoice_number = f"INV-{timezone.now():%Y%m%d}-{uuid4().hex[:6].upper()}"
        invoice = self.invoice_repo.create_invoice(
            user=user,
            invoice_number=invoice_number,
            total_amount=package.price,
            status=InvoiceStatus.UNPAID,
        )
        self.invoice_repo.create_invoice_item(
            invoice=invoice,
            item_type=InvoiceItemType.MEMBERSHIP,
            object_id=membership.id,
            amount=package.price,
        )

        return membership

    def cancel_membership(self, user, membership_id):
        membership = self.membership_repo.get_user_membership_by_id(user, membership_id)
        if not membership:
            raise GymException("Membership not found.")

        old_status = membership.status
        membership.status = MembershipStatus.CANCELLED
        membership.save(update_fields=["status"])

        # Also cancel any unpaid invoice/payment for this membership if it was pending
        if old_status == MembershipStatus.PENDING:
            invoice_item = self.invoice_repo.get_invoice_item_by_membership(membership.id)
            if invoice_item and invoice_item.invoice:
                invoice = invoice_item.invoice
                if invoice.status == InvoiceStatus.UNPAID:
                    invoice.status = InvoiceStatus.CANCELLED
                    invoice.save(update_fields=["status", "updated_at"])

                    # Update associated payments to failed via queryset
                    from gym_booking_backend.infrastructure.models import Payment
                    Payment.objects.filter(invoice=invoice, status=PaymentStatus.PENDING).update(
                        status=PaymentStatus.FAILED
                    )

        return membership

    def expire_old_memberships(self):
        today = timezone.localdate()
        return self.membership_repo.expire_memberships_before(today)

    def get_my_memberships(self, user):
        return self.membership_repo.get_user_memberships(user)

    def get_active_packages(self):
        return self.membership_repo.get_active_packages()

    @transaction.atomic
    def freeze_membership(self, user, membership_id, start_date, end_date, reason=""):
        from datetime import datetime
        from gym_booking_backend.infrastructure.models import MembershipFreeze

        membership = self.membership_repo.get_user_membership_by_id(user, membership_id)
        if not membership:
            raise GymException("Membership not found.")
        if membership.status != MembershipStatus.ACTIVE:
            raise GymException("Only active memberships can be frozen.")

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        if start_date >= end_date:
            raise GymException("Start date must be before end date.")
        if start_date < timezone.localdate():
            raise GymException("Freeze start date cannot be in the past.")

        duration_days = (end_date - start_date).days
        package = membership.package
        if not package.is_freezable:
            raise GymException("This membership package is not freezable.")

        existing_freeze_days = sum(f.duration_days for f in membership.freezes.all())
        if existing_freeze_days + duration_days > package.max_freeze_days:
            raise GymException(f"Freeze duration exceeds maximum allowed days ({package.max_freeze_days} days).")

        freeze = MembershipFreeze.objects.create(
            user_membership=membership,
            start_date=start_date,
            end_date=end_date,
            duration_days=duration_days,
            reason=reason,
        )

        membership.end_date += timedelta(days=duration_days)
        membership.save(update_fields=["end_date"])
        return freeze


# Backward compatibility instance and delegates
_service = MembershipService(membership_repository, invoice_repository, payment_repository)
create_membership = _service.create_membership
cancel_membership = _service.cancel_membership
expire_old_memberships = _service.expire_old_memberships
get_my_memberships = _service.get_my_memberships
get_active_packages = _service.get_active_packages
freeze_membership = _service.freeze_membership
