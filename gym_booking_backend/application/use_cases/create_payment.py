from gym_booking_backend.application.services import payment_service


def execute(user, membership_id, payment_method):
    return payment_service.create_payment(user, membership_id, payment_method)

