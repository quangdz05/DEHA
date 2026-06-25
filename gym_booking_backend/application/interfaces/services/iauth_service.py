from abc import ABC, abstractmethod
from gym_booking_backend.domain.result import Result


class IAuthService(ABC):
    @abstractmethod
    def register_user(self, username, email, password, first_name="", last_name="", role="member") -> Result:
        pass

    @abstractmethod
    def login_user(self, request, username, password) -> Result:
        pass

    @abstractmethod
    def logout_user(self, request) -> Result:
        pass
