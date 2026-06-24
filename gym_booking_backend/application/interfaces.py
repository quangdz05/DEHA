from abc import ABC, abstractmethod

class IUserRepository(ABC):
    @abstractmethod
    def get_user_by_id(self, user_id):
        pass

    @abstractmethod
    def get_user_by_username(self, username):
        pass

    @abstractmethod
    def create_user(self, username, email, password, first_name="", last_name=""):
        pass


class IBookingRepository(ABC):
    @abstractmethod
    def get_booking_by_id(self, booking_id):
        pass

    @abstractmethod
    def get_next_waitlisted_booking(self, schedule_id, select_for_update=False):
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
    def create_booking(self, user, schedule, booking_code, note="", status=None):
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
    def has_completed_booking_for_trainer(self, user, trainer_id):
        pass

    @abstractmethod
    def has_completed_booking_for_class(self, user, gym_class_id):
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


class IClassRepository(ABC):
    @abstractmethod
    def get_all_categories(self):
        pass

    @abstractmethod
    def get_all_classes(self):
        pass

    @abstractmethod
    def get_class_by_id(self, class_id):
        pass

    @abstractmethod
    def get_classes_by_category(self, category_id):
        pass

    @abstractmethod
    def get_classes_by_trainer(self, trainer_id):
        pass


class IMembershipRepository(ABC):
    @abstractmethod
    def get_package_by_id(self, package_id):
        pass

    @abstractmethod
    def get_active_packages(self):
        pass

    @abstractmethod
    def get_active_membership(self, user):
        pass

    @abstractmethod
    def has_active_membership(self, user):
        pass

    @abstractmethod
    def create_user_membership(self, user, package, start_date, end_date):
        pass

    @abstractmethod
    def get_user_membership_by_id(self, user, membership_id):
        pass

    @abstractmethod
    def get_user_memberships(self, user):
        pass

    @abstractmethod
    def expire_memberships_before(self, date):
        pass

    @abstractmethod
    def has_active_or_pending_membership(self, user):
        pass


class IPaymentRepository(ABC):
    @abstractmethod
    def get_payment_by_id(self, payment_id):
        pass

    @abstractmethod
    def get_user_payments(self, user):
        pass

    @abstractmethod
    def create_payment(self, user, membership, amount, payment_method, transaction_code=None, invoice=None):
        pass


class IProfileRepository(ABC):
    @abstractmethod
    def get_profile_by_user(self, user):
        pass

    @abstractmethod
    def update_profile(self, user, **data):
        pass


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


class IReviewRepository(ABC):
    @abstractmethod
    def get_review_by_id(self, review_id):
        pass

    @abstractmethod
    def get_reviews_by_trainer(self, trainer_id):
        pass

    @abstractmethod
    def get_reviews_by_class(self, gym_class_id):
        pass

    @abstractmethod
    def has_user_reviewed_trainer(self, user, trainer):
        pass

    @abstractmethod
    def has_user_reviewed_class(self, user, gym_class):
        pass

    @abstractmethod
    def create_review(self, user, trainer=None, gym_class=None, rating=5, comment=""):
        pass


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


class ITrainerRepository(ABC):
    @abstractmethod
    def get_all_trainers(self):
        pass

    @abstractmethod
    def get_active_trainers(self):
        pass

    @abstractmethod
    def get_trainer_by_id(self, trainer_id, select_for_update=False):
        pass

    @abstractmethod
    def get_trainer_by_user(self, user):
        pass

    @abstractmethod
    def create_trainer(self, user, name, email, phone="", specialty="General Trainer", experience_years=1):
        pass


class IInvoiceRepository(ABC):
    @abstractmethod
    def create_invoice(self, user, invoice_number, total_amount, status):
        pass

    @abstractmethod
    def create_invoice_item(self, invoice, item_type, object_id, amount):
        pass

    @abstractmethod
    def get_invoice_item_by_membership(self, membership_id):
        pass

    @abstractmethod
    def get_invoice_item_by_class_fee(self, booking_id):
        pass
