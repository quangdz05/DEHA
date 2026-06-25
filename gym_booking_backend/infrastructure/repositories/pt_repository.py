import datetime
from django.db.models import Q
from gym_booking_backend.domain.constants import BookingStatus, PTBookingStatus, ScheduleStatus
from gym_booking_backend.infrastructure.models import (
    PTPackage,
    TrainerSchedule,
    UserPTPackage,
    PTBooking,
    TrainerBooking,
    Booking,
    ClassSchedule,
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

        # 3. Overlap with ClassSchedule
        class_overlap = ClassSchedule.objects.filter(
            trainer=trainer,
            start_time__date=booking_date,
            status__in=[ScheduleStatus.OPEN, ScheduleStatus.FULL],
            start_time__time__lt=end_time,
            end_time__time__gt=start_time,
        ).exists()
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

        # 3. Overlap with Gym Class Booking
        class_overlap = Booking.objects.filter(
            user=user,
            status__in=ACTIVE_BOOKING_STATUSES,
            schedule__start_time__date=booking_date,
            schedule__start_time__time__lt=end_time,
            schedule__end_time__time__gt=start_time,
        ).exists()
        return class_overlap


pt_repository = DjangoPTRepository()
