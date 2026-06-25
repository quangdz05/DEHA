from datetime import datetime

from gym_booking_backend.domain.exceptions import GymException
from gym_booking_backend.infrastructure.repositories.schedule_repository import schedule_repository
from gym_booking_backend.application.interfaces.services.ischedule_service import IScheduleService
from gym_booking_backend.domain.result import Result


class ScheduleService(IScheduleService):
    def get_schedules(self, date=None, trainer_id=None, available=False) -> Result:
        try:
            if date:
                try:
                    parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
                except ValueError as exc:
                    return Result.failure_result("Date must use YYYY-MM-DD format.", status_code=400)
                schedules = schedule_repository.get_schedules_by_date(parsed_date)
            elif trainer_id:
                schedules = schedule_repository.get_schedules_by_trainer(trainer_id)
            elif available:
                schedules = schedule_repository.get_schedules_with_available_slots()
            else:
                schedules = schedule_repository.get_all_schedules()
            return Result.success_result(schedules, status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def get_schedule(self, schedule_id) -> Result:
        schedule = schedule_repository.get_schedule_by_id(schedule_id)
        if not schedule:
            return Result.failure_result("Schedule not found", status_code=404)
        return Result.success_result(schedule, status_code=200)


schedule_service = ScheduleService()
