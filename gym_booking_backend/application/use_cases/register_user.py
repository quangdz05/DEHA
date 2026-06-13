from gym_booking_backend.application.services import auth_service


def execute(username, email, password, first_name="", last_name="", role="member"):
    return auth_service.register_user(username, email, password, first_name, last_name, role)

