from gym_booking_backend.application.services import membership_service


def execute(user, package_id):
    return membership_service.create_membership(user, package_id)

