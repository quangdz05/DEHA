from abc import ABC, abstractmethod
from gym_booking_backend.domain.result import Result


class IMembershipService(ABC):
    @abstractmethod
    def create_membership(self, user, package_id) -> Result:
        pass

    @abstractmethod
    def cancel_membership(self, user, membership_id) -> Result:
        pass

    @abstractmethod
    def expire_old_memberships(self) -> Result:
        pass

    @abstractmethod
    def get_my_memberships(self, user) -> Result:
        pass

    @abstractmethod
    def get_active_packages(self) -> Result:
        pass

    @abstractmethod
    def freeze_membership(self, user, membership_id, start_date, end_date, reason="") -> Result:
        pass
