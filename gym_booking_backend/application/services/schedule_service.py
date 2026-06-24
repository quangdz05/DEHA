from datetime import datetime

from gym_booking_backend.domain.exceptions import InvalidScheduleException
from gym_booking_backend.infrastructure.repositories import schedule_repository


class ScheduleService:
    def __init__(self, schedule_repo):
        self.schedule_repo = schedule_repo

    def get_schedules(self, date=None, trainer_id=None, available=False):
        if date:
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError as exc:
                raise InvalidScheduleException("Date must use YYYY-MM-DD format.") from exc
            return self.schedule_repo.get_schedules_by_date(parsed_date)
        if trainer_id:
            return self.schedule_repo.get_schedules_by_trainer(trainer_id)
        if available:
            return self.schedule_repo.get_schedules_with_available_slots()
        return self.schedule_repo.get_all_schedules()

    def get_schedule(self, schedule_id):
        return self.schedule_repo.get_schedule_by_id(schedule_id)


# Backward compatibility instance and delegates
_service = ScheduleService(schedule_repository)
get_schedules = _service.get_schedules
get_schedule = _service.get_schedule
