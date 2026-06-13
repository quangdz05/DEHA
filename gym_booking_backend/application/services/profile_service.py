from gym_booking_backend.infrastructure.repositories import profile_repository


def get_my_profile(user):
    profile = profile_repository.get_profile_by_user(user)
    if profile:
        return profile
    return profile_repository.update_profile(user, full_name=user.get_full_name() or user.username)


def update_my_profile(user, data):
    return profile_repository.update_profile(user, **data)

