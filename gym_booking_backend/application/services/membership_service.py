from datetime import timedelta
from django.db import transaction
from django.utils import timezone

from gym_booking_backend.application.validators import membership_validator
from gym_booking_backend.domain.constants import MembershipStatus, UserRole
from gym_booking_backend.domain.exceptions import GymException
from gym_booking_backend.infrastructure.repositories import membership_repository


@transaction.atomic
def create_membership(user, package_id):
    # Validate user is a member
    if not hasattr(user, "profile") or user.profile.role != UserRole.MEMBER:
        raise GymException("Chỉ có hội viên mới được đăng ký gói tập.")

    package = membership_repository.get_package_by_id(package_id)
    if not package:
        raise GymException("Membership package not found.")

    # Validate user has no active or pending membership
    from gym_booking_backend.infrastructure.models import UserMembership
    has_active_or_pending = UserMembership.objects.filter(
        user=user,
        status__in=[MembershipStatus.ACTIVE, MembershipStatus.PENDING]
    ).exists()
    if has_active_or_pending:
        raise GymException("Bạn đã có gói tập đang hoạt động hoặc chờ thanh toán.")

    start_date = timezone.localdate()
    end_date = start_date + timedelta(days=package.duration_days)
    membership_validator.validate_membership_dates(start_date, end_date)
    
    membership = membership_repository.create_user_membership(user, package, start_date, end_date)

    # Automatically create Invoice and InvoiceItem
    from gym_booking_backend.infrastructure.models import Invoice, InvoiceItem, InvoiceStatus, InvoiceItemType
    from uuid import uuid4
    invoice_number = f"INV-{timezone.now():%Y%m%d}-{uuid4().hex[:6].upper()}"
    invoice = Invoice.objects.create(
        user=user,
        invoice_number=invoice_number,
        total_amount=package.price,
        status=InvoiceStatus.UNPAID
    )
    InvoiceItem.objects.create(
        invoice=invoice,
        item_type=InvoiceItemType.MEMBERSHIP,
        object_id=membership.id,
        amount=package.price
    )

    return membership


def cancel_membership(user, membership_id):
    membership = membership_repository.get_user_membership_by_id(user, membership_id)
    if not membership:
        raise GymException("Membership not found.")
    
    old_status = membership.status
    membership.status = MembershipStatus.CANCELLED
    membership.save(update_fields=["status"])

    # Also cancel any unpaid invoice/payment for this membership if it was pending
    if old_status == MembershipStatus.PENDING:
        from gym_booking_backend.infrastructure.models import InvoiceItem, InvoiceStatus, Payment, PaymentStatus
        invoice_item = InvoiceItem.objects.filter(item_type=InvoiceItemType.MEMBERSHIP, object_id=membership.id).first()
        if invoice_item and invoice_item.invoice:
            invoice = invoice_item.invoice
            if invoice.status == InvoiceStatus.UNPAID:
                invoice.status = InvoiceStatus.CANCELLED
                invoice.save(update_fields=["status", "updated_at"])
                
                # Update associated payments to failed
                Payment.objects.filter(invoice=invoice, status=PaymentStatus.PENDING).update(status=PaymentStatus.FAILED)

    return membership


def expire_old_memberships():
    today = timezone.localdate()
    return membership_repository.expire_memberships_before(today)


def get_my_memberships(user):
    return membership_repository.get_user_memberships(user)


def get_active_packages():
    return membership_repository.get_active_packages()


@transaction.atomic
def freeze_membership(user, membership_id, start_date, end_date, reason=""):
    from datetime import datetime
    from gym_booking_backend.infrastructure.models import UserMembership, MembershipFreeze

    membership = UserMembership.objects.filter(id=membership_id, user=user).first()
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
        reason=reason
    )

    membership.end_date += timedelta(days=duration_days)
    membership.save(update_fields=["end_date"])
    return freeze
