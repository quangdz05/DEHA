from gym_booking_backend.infrastructure.models import Profile
from gym_booking_backend.application.interfaces.repositories.iprofile_repository import IProfileRepository


class DjangoProfileRepository(IProfileRepository):
    def get_profile_by_user(self, user):
        return Profile.objects.filter(user=user).first()

    def update_profile(self, user, **data):
        profile, _ = Profile.objects.get_or_create(
            user=user,
            defaults={"full_name": data.get("full_name") or user.get_full_name() or user.username},
        )
        for field, value in data.items():
            setattr(profile, field, value)
        profile.save()
        return profile


profile_repository = DjangoProfileRepository()
