from gym_booking_backend.infrastructure.repositories.profile_repository import profile_repository
from gym_booking_backend.application.interfaces.services.iprofile_service import IProfileService
from gym_booking_backend.domain.result import Result


class ProfileService(IProfileService):
    def get_my_profile(self, user) -> Result:
        profile = profile_repository.get_profile_by_user(user)
        if not profile:
            profile = profile_repository.update_profile(user, full_name=user.get_full_name() or user.username)
        return Result.success_result(profile, status_code=200)

    def update_my_profile(self, user, data) -> Result:
        profile = profile_repository.update_profile(user, **data)
        return Result.success_result(profile, status_code=200)


profile_service = ProfileService()
