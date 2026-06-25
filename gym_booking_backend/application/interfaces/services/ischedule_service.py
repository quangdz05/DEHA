from abc import ABC, abstractmethod
from gym_booking_backend.domain.result import Result


class IScheduleService(ABC):
    @abstractmethod
    def get_schedules(self, date=None, trainer_id=None, available=False) -> Result:
        pass

    @abstractmethod
    def get_schedule(self, schedule_id) -> Result:
        pass
