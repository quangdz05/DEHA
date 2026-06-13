from datetime import datetime

from gym_booking_backend.domain.exceptions import InvalidScheduleException
from gym_booking_backend.infrastructure.repositories import schedule_repository


def get_schedules(date=None, trainer_id=None, available=False):
    if date:
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError as exc:
            raise InvalidScheduleException("Date must use YYYY-MM-DD format.") from exc
        return schedule_repository.get_schedules_by_date(parsed_date)
    if trainer_id:
        return schedule_repository.get_schedules_by_trainer(trainer_id)
    if available:
        return schedule_repository.get_schedules_with_available_slots()
    return schedule_repository.get_all_schedules()


def get_schedule(schedule_id):
    return schedule_repository.get_schedule_by_id(schedule_id)
