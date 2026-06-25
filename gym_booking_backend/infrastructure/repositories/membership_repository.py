from django.utils import timezone

from gym_booking_backend.domain.constants import CommonStatus, MembershipStatus
from gym_booking_backend.infrastructure.models import MembershipPackage, UserMembership
from gym_booking_backend.application.interfaces.repositories.imembership_repository import IMembershipRepository


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


membership_repository = DjangoMembershipRepository()
