from gym_booking_backend.application.interfaces.repositories.ischedule_repository import IScheduleRepository


class DjangoScheduleRepository(IScheduleRepository):
    def get_schedule_by_id(self, schedule_id, select_for_update=False):
        return None

    def get_available_schedules(self):
        return []

    def get_all_schedules(self):
        return []

    def get_schedules_by_date(self, date):
        return []

    def get_schedules_by_trainer(self, trainer_id):
        return []

    def get_schedules_with_available_slots(self):
        return []

    def has_room_conflict(self, room, start_time, end_time, exclude_id=None):
        return False

    def has_trainer_conflict(self, trainer, start_time, end_time, exclude_id=None):
        return False

    def get_unassigned_schedules(self):
        return []


schedule_repository = DjangoScheduleRepository()
