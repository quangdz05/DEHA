from gym_booking_backend.application.services import booking_service


def execute(user, booking_id, cancellation_reason=""):
    return booking_service.cancel_booking(user, booking_id, cancellation_reason)

