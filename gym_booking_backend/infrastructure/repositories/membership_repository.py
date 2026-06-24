from django.utils import timezone
from gym_booking_backend.domain.constants import CommonStatus, MembershipStatus
from gym_booking_backend.application.interfaces import IMembershipRepository
from gym_booking_backend.infrastructure.models import MembershipPackage, UserMembership


class DjangoMembershipRepository(IMembershipRepository):
    def get_package_by_id(self, package_id):
        return MembershipPackage.objects.filter(id=package_id).first()

    def get_active_packages(self):
        return MembershipPackage.objects.filter(status=CommonStatus.ACTIVE)

    def get_active_membership(self, user):
        today = timezone.localdate()
        return (
            UserMembership.objects.select_related("package")
            .filter(user=user, status=MembershipStatus.ACTIVE, start_date__lte=today, end_date__gte=today)
            .order_by("-created_at")
            .first()
        )

    def has_active_membership(self, user):
        return self.get_active_membership(user) is not None

    def create_user_membership(self, user, package, start_date, end_date):
        return UserMembership.objects.create(user=user, package=package, start_date=start_date, end_date=end_date)

    def get_user_membership_by_id(self, user, membership_id):
        return UserMembership.objects.select_related("package").filter(id=membership_id, user=user).first()

    def get_user_memberships(self, user):
        return UserMembership.objects.select_related("package").filter(user=user)

    def expire_memberships_before(self, date):
        return UserMembership.objects.filter(status=MembershipStatus.ACTIVE, end_date__lt=date).update(
            status=MembershipStatus.EXPIRED
        )

    def has_active_or_pending_membership(self, user):
        return UserMembership.objects.filter(
            user=user,
            status__in=[MembershipStatus.ACTIVE, MembershipStatus.PENDING]
        ).exists()


# Backward compatibility exports
_instance = DjangoMembershipRepository()
get_package_by_id = _instance.get_package_by_id
get_active_packages = _instance.get_active_packages
get_active_membership = _instance.get_active_membership
has_active_membership = _instance.has_active_membership
create_user_membership = _instance.create_user_membership
get_user_membership_by_id = _instance.get_user_membership_by_id
get_user_memberships = _instance.get_user_memberships
expire_memberships_before = _instance.expire_memberships_before
has_active_or_pending_membership = _instance.has_active_or_pending_membership

