from abc import ABC, abstractmethod


class IScheduleRepository(ABC):
    @abstractmethod
    def get_schedule_by_id(self, schedule_id, select_for_update=False):
        pass

    @abstractmethod
    def get_available_schedules(self):
        pass

    @abstractmethod
    def get_all_schedules(self):
        pass

    @abstractmethod
    def get_schedules_by_date(self, date):
        pass

    @abstractmethod
    def get_schedules_by_trainer(self, trainer_id):
        pass

    @abstractmethod
    def get_schedules_with_available_slots(self):
        pass

    @abstractmethod
    def has_room_conflict(self, room, start_time, end_time, exclude_id=None):
        pass

    @abstractmethod
    def has_trainer_conflict(self, trainer, start_time, end_time, exclude_id=None):
        pass
