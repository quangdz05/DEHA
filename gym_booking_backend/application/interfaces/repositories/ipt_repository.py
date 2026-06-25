from abc import ABC, abstractmethod


class IPTRepository(ABC):
    @abstractmethod
    def get_active_pt_packages(self):
        pass

    @abstractmethod
    def get_pt_package_by_id(self, package_id):
        pass

    @abstractmethod
    def get_trainer_schedules(self, trainer):
        pass

    @abstractmethod
    def get_trainer_schedule_for_weekday(self, trainer, weekday):
        pass

    @abstractmethod
    def get_user_pt_packages(self, user):
        pass

    @abstractmethod
    def get_user_pt_package_detail(self, pk, user=None):
        pass

    @abstractmethod
    def get_pt_bookings_for_package(self, user_pt_package):
        pass

    @abstractmethod
    def has_trainer_pt_booking_conflict(self, trainer, booking_date, start_time, end_time):
        pass

    @abstractmethod
    def has_user_pt_booking_conflict(self, user, booking_date, start_time, end_time):
        pass

    @abstractmethod
    def has_active_pt_package(self, user):
        pass

    @abstractmethod
    def create_user_pt_package(self, user, trainer, package, start_date, end_date, total_sessions, weekdays_list, start_time, end_time):
        pass

    @abstractmethod
    def create_pt_booking(self, user, trainer, user_pt_package, booking_code, booking_date, start_time, end_time, status, note=""):
        pass

    @abstractmethod
    def get_pt_booking_by_id(self, booking_id, select_for_update=False):
        pass

    @abstractmethod
    def get_user_pt_package_by_id(self, package_id, select_for_update=False):
        pass

    @abstractmethod
    def cancel_active_bookings_for_package(self, user_pt_package):
        pass
