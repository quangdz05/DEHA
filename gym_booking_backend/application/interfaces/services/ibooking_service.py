from abc import ABC, abstractmethod
from gym_booking_backend.domain.result import Result


class IBookingService(ABC):
    @abstractmethod
    def create_booking(self, user, schedule_id, note="") -> Result:
        pass

    @abstractmethod
    def cancel_booking(self, user, booking_id, cancellation_reason="") -> Result:
        pass

    @abstractmethod
    def complete_booking(self, booking_id) -> Result:
        pass

    @abstractmethod
    def mark_no_show(self, booking_id) -> Result:
        pass

    @abstractmethod
    def get_my_bookings(self, user) -> Result:
        pass

    @abstractmethod
    def create_trainer_booking(self, user, trainer_id, start_time, end_time, note="") -> Result:
        pass

    @abstractmethod
    def cancel_trainer_booking(self, user, booking_id, cancellation_reason="") -> Result:
        pass

    @abstractmethod
    def get_my_trainer_bookings(self, user) -> Result:
        pass

    @abstractmethod
    def get_trainer_personal_bookings(self, user) -> Result:
        pass

    @abstractmethod
    def update_trainer_booking_status(self, user, booking_id, new_status) -> Result:
        pass

    @abstractmethod
    def get_my_trainer_monthly_bookings(self, user) -> Result:
        pass

    @abstractmethod
    def get_trainer_monthly_bookings(self, user) -> Result:
        pass

    @abstractmethod
    def get_all_trainer_monthly_bookings(self, user) -> Result:
        pass

    @abstractmethod
    def update_trainer_monthly_booking_status(self, user, booking_id, new_status) -> Result:
        pass

    @abstractmethod
    def create_trainer_monthly_booking(self, user, trainer_id, start_date, months=1, sessions_per_week=3, preferred_time=None, note="") -> Result:
        pass

    @abstractmethod
    def update_admin_trainer_monthly_booking_status(self, booking_id, new_status) -> Result:
        pass
