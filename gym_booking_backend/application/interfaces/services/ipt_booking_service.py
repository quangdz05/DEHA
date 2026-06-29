from abc import ABC, abstractmethod
from gym_booking_backend.domain.result import Result


class IPTBookingService(ABC):
    @abstractmethod
    def preview_monthly_pt_bookings(self, user, months, trainer_id, start_date, selected_weekdays, start_time, end_time) -> Result:
        pass

    @abstractmethod
    def create_monthly_pt_bookings(self, user, months, trainer_id, start_date, selected_weekdays, start_time, end_time, note="") -> Result:
        pass

    @abstractmethod
    def complete_pt_booking(self, booking_id) -> Result:
        pass

    @abstractmethod
    def cancel_pt_booking(self, booking_id) -> Result:
        pass

    @abstractmethod
    def cancel_user_pt_package(self, user_pt_package_id) -> Result:
        pass
