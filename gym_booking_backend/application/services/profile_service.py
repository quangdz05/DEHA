from gym_booking_backend.infrastructure.repositories import profile_repository


class ProfileService:
    def __init__(self, profile_repo):
        self.profile_repo = profile_repo

    def get_my_profile(self, user):
        profile = self.profile_repo.get_profile_by_user(user)
        if profile:
            return profile
        return self.profile_repo.update_profile(user, full_name=user.get_full_name() or user.username)

    def update_my_profile(self, user, data):
        return self.profile_repo.update_profile(user, **data)


# Backward compatibility instance and delegates
_service = ProfileService(profile_repository)
get_my_profile = _service.get_my_profile
update_my_profile = _service.update_my_profile
