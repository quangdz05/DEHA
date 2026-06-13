from gym_booking_backend.application.services import booking_service


def execute(user, schedule_id, note=""):
    return booking_service.create_booking(user, schedule_id, note)

