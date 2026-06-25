from abc import ABC, abstractmethod
from gym_booking_backend.domain.result import Result


class IProfileService(ABC):
    @abstractmethod
    def get_my_profile(self, user) -> Result:
        pass

    @abstractmethod
    def update_my_profile(self, user, data) -> Result:
        pass
