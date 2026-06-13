from django.utils import timezone

from gym_booking_backend.domain.constants import CommonStatus, MembershipStatus
from gym_booking_backend.infrastructure.models import MembershipPackage, UserMembership


def get_package_by_id(package_id):
    return MembershipPackage.objects.filter(id=package_id).first()


def get_active_packages():
    return MembershipPackage.objects.filter(status=CommonStatus.ACTIVE)


def get_active_membership(user):
    today = timezone.localdate()
    return (
        UserMembership.objects.select_related("package")
        .filter(user=user, status=MembershipStatus.ACTIVE, start_date__lte=today, end_date__gte=today)
        .order_by("-created_at")
        .first()
    )


def has_active_membership(user):
    return get_active_membership(user) is not None


def create_user_membership(user, package, start_date, end_date):
    return UserMembership.objects.create(user=user, package=package, start_date=start_date, end_date=end_date)


def get_user_membership_by_id(user, membership_id):
    return UserMembership.objects.select_related("package").filter(id=membership_id, user=user).first()


def get_user_memberships(user):
    return UserMembership.objects.select_related("package").filter(user=user)


def expire_memberships_before(date):
    return UserMembership.objects.filter(status=MembershipStatus.ACTIVE, end_date__lt=date).update(
        status=MembershipStatus.EXPIRED
    )
