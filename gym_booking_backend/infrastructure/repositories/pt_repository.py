import datetime
from django.db.models import Q
from gym_booking_backend.domain.constants import BookingStatus, PTBookingStatus, ScheduleStatus
from gym_booking_backend.infrastructure.models import (
    PTPackage,
    TrainerSchedule,
    UserPTPackage,
    PTBooking,
    TrainerBooking,
)
from gym_booking_backend.application.interfaces.repositories.ipt_repository import IPTRepository

ACTIVE_BOOKING_STATUSES = [BookingStatus.PENDING, BookingStatus.CONFIRMED]
ACTIVE_PT_BOOKING_STATUSES = [PTBookingStatus.PENDING, PTBookingStatus.CONFIRMED]


class DjangoPTRepository(IPTRepository):
    def get_active_pt_packages(self):
        return PTPackage.objects.filter(is_active=True)

    def get_pt_package_by_id(self, package_id):
        return PTPackage.objects.filter(id=package_id).first()

    def get_trainer_schedules(self, trainer):
        return TrainerSchedule.objects.filter(trainer=trainer, is_available=True)

    def get_trainer_schedule_for_weekday(self, trainer, weekday):
        return TrainerSchedule.objects.filter(trainer=trainer, weekday=weekday, is_available=True).first()

    def get_user_pt_packages(self, user):
        return UserPTPackage.objects.select_related("trainer", "package").filter(user=user)

    def get_user_pt_package_detail(self, pk, user=None):
        query = UserPTPackage.objects.select_related("trainer", "package")
        if user:
            query = query.filter(user=user)
        return query.filter(id=pk).first()

    def get_pt_bookings_for_package(self, user_pt_package):
        return PTBooking.objects.filter(user_pt_package=user_pt_package)

    def has_trainer_pt_booking_conflict(self, trainer, booking_date, start_time, end_time):
        # 1. Overlap with PTBooking
        pt_overlap = PTBooking.objects.filter(
            trainer=trainer,
            booking_date=booking_date,
            status__in=ACTIVE_PT_BOOKING_STATUSES,
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).exists()
        if pt_overlap:
            return True

        # 2. Overlap with TrainerBooking
        trainer_overlap = TrainerBooking.objects.filter(
            trainer=trainer,
            start_time__date=booking_date,
            status__in=ACTIVE_BOOKING_STATUSES,
            start_time__time__lt=end_time,
            end_time__time__gt=start_time,
        ).exists()
        if trainer_overlap:
            return True

        # 3. Overlap with ClassSchedule (N/A)
        class_overlap = False
        return class_overlap

    def has_user_pt_booking_conflict(self, user, booking_date, start_time, end_time):
        # 1. Overlap with PTBooking
        pt_overlap = PTBooking.objects.filter(
            user=user,
            booking_date=booking_date,
            status__in=ACTIVE_PT_BOOKING_STATUSES,
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).exists()
        if pt_overlap:
            return True

        # 2. Overlap with TrainerBooking
        trainer_overlap = TrainerBooking.objects.filter(
            user=user,
            start_time__date=booking_date,
            status__in=ACTIVE_BOOKING_STATUSES,
            start_time__time__lt=end_time,
            end_time__time__gt=start_time,
        ).exists()
        if trainer_overlap:
            return True

        # 3. Overlap with Gym Class Booking (N/A)
        class_overlap = False
        return class_overlap

    def has_active_pt_package(self, user):
        from gym_booking_backend.domain.constants import UserPTPackageStatus
        return UserPTPackage.objects.filter(user=user, status=UserPTPackageStatus.ACTIVE).exists()

    def create_user_pt_package(self, user, trainer, package, start_date, end_date, total_sessions, weekdays_list, start_time, end_time):
        from gym_booking_backend.domain.constants import UserPTPackageStatus
        return UserPTPackage.objects.create(
            user=user,
            trainer=trainer,
            package=package,
            start_date=start_date,
            end_date=end_date,
            total_sessions=total_sessions,
            used_sessions=0,
            status=UserPTPackageStatus.ACTIVE,
            selected_weekdays=weekdays_list,
            start_time=start_time,
            end_time=end_time,
        )

    def create_pt_booking(self, user, trainer, user_pt_package, booking_code, booking_date, start_time, end_time, status, note=""):
        return PTBooking.objects.create(
            user=user,
            trainer=trainer,
            user_pt_package=user_pt_package,
            booking_code=booking_code,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            status=status,
            note=note,
        )

    def get_pt_booking_by_id(self, booking_id, select_for_update=False):
        queryset = PTBooking.objects.filter(id=booking_id)
        if select_for_update:
            queryset = queryset.select_for_update()
        return queryset.first()

    def get_user_pt_package_by_id(self, package_id, select_for_update=False):
        queryset = UserPTPackage.objects.filter(id=package_id)
        if select_for_update:
            queryset = queryset.select_for_update()
        return queryset.first()

    def cancel_active_bookings_for_package(self, user_pt_package):
        from gym_booking_backend.domain.constants import PTBookingStatus
        return PTBooking.objects.filter(
            user_pt_package=user_pt_package,
            status__in=[PTBookingStatus.PENDING, PTBookingStatus.CONFIRMED],
        ).update(status=PTBookingStatus.CANCELLED)


pt_repository = DjangoPTRepository()
