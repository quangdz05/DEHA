from abc import ABC, abstractmethod


class IBookingRepository(ABC):
    @abstractmethod
    def get_booking_by_id(self, booking_id):
        pass

    @abstractmethod
    def get_user_bookings(self, user):
        pass

    @abstractmethod
    def has_duplicate_booking(self, user, schedule):
        pass

    @abstractmethod
    def has_overlapping_booking(self, user, schedule):
        pass

    @abstractmethod
    def has_user_overlapping_time(self, user, start_time, end_time, trainer_booking_id=None):
        pass

    @abstractmethod
    def has_trainer_overlapping_time(self, trainer, start_time, end_time, trainer_booking_id=None):
        pass

    @abstractmethod
    def create_booking(self, user, schedule, booking_code, note=""):
        pass

    @abstractmethod
    def count_user_bookings_in_week(self, user, start_dt, end_dt):
        pass

    @abstractmethod
    def get_user_trainer_bookings(self, user):
        pass

    @abstractmethod
    def get_trainer_personal_bookings(self, trainer):
        pass

    @abstractmethod
    def get_trainer_booking_by_id(self, booking_id):
        pass

    @abstractmethod
    def create_trainer_booking(self, user, trainer, booking_code, start_time, end_time, note=""):
        pass

    @abstractmethod
    def get_user_trainer_monthly_bookings(self, user):
        pass

    @abstractmethod
    def get_trainer_monthly_bookings(self, trainer):
        pass

    @abstractmethod
    def get_all_trainer_monthly_bookings(self):
        pass

    @abstractmethod
    def get_trainer_monthly_booking_by_id(self, booking_id):
        pass

    @abstractmethod
    def has_overlapping_monthly_booking(self, user, trainer, start_date, end_date, booking_id=None):
        pass

    @abstractmethod
    def create_trainer_monthly_booking(self, user, trainer, booking_code, start_date, end_date, months, sessions_per_week, preferred_time=None, note=""):
        pass
