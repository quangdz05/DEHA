from gym_booking_backend.application.services import profile_service


def execute(user, data):
    return profile_service.update_my_profile(user, data)

