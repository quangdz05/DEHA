from django.db.models import Q

from gym_booking_backend.domain.constants import BookingStatus, PTBookingStatus
from gym_booking_backend.infrastructure.models import Booking, TrainerBooking, TrainerMonthlyBooking, PTBooking
from gym_booking_backend.application.interfaces.repositories.ibooking_repository import IBookingRepository

ACTIVE_BOOKING_STATUSES = [BookingStatus.PENDING, BookingStatus.CONFIRMED]


class DjangoBookingRepository(IBookingRepository):
    def get_booking_by_id(self, booking_id):
        return Booking.objects.select_related("schedule", "schedule__gym_class", "schedule__trainer", "schedule__room").filter(id=booking_id).first()

    def get_user_bookings(self, user):
        return Booking.objects.select_related("schedule", "schedule__gym_class", "schedule__trainer", "schedule__room").filter(user=user)

    def has_duplicate_booking(self, user, schedule):
        return Booking.objects.filter(user=user, schedule=schedule, status__in=ACTIVE_BOOKING_STATUSES).exists()

    def has_overlapping_booking(self, user, schedule):
        class_overlap = Booking.objects.filter(user=user, status__in=ACTIVE_BOOKING_STATUSES).filter(
            Q(schedule__start_time__lt=schedule.end_time) & Q(schedule__end_time__gt=schedule.start_time)
        ).exists()
        trainer_overlap = TrainerBooking.objects.filter(user=user, status__in=ACTIVE_BOOKING_STATUSES).filter(
            Q(start_time__lt=schedule.end_time) & Q(end_time__gt=schedule.start_time)
        ).exists()
        
        booking_date = schedule.start_time.date()
        pt_start = schedule.start_time.time()
        pt_end = schedule.end_time.time()
        pt_overlap = PTBooking.objects.filter(
            user=user,
            booking_date=booking_date,
            status=PTBookingStatus.CONFIRMED,
            start_time__lt=pt_end,
            end_time__gt=pt_start,
        ).exists()
        
        return class_overlap or trainer_overlap or pt_overlap

    def has_user_overlapping_time(self, user, start_time, end_time, trainer_booking_id=None):
        class_overlap = Booking.objects.filter(user=user, status__in=ACTIVE_BOOKING_STATUSES).filter(
            Q(schedule__start_time__lt=end_time) & Q(schedule__end_time__gt=start_time)
        ).exists()

        trainer_query = TrainerBooking.objects.filter(user=user, status__in=ACTIVE_BOOKING_STATUSES).filter(
            Q(start_time__lt=end_time) & Q(end_time__gt=start_time)
        )
        if trainer_booking_id:
            trainer_query = trainer_query.exclude(id=trainer_booking_id)

        booking_date = start_time.date()
        pt_start = start_time.time()
        pt_end = end_time.time()
        pt_overlap = PTBooking.objects.filter(
            user=user,
            booking_date=booking_date,
            status=PTBookingStatus.CONFIRMED,
            start_time__lt=pt_end,
            end_time__gt=pt_start,
        ).exists()

        return class_overlap or trainer_query.exists() or pt_overlap

    def has_trainer_overlapping_time(self, trainer, start_time, end_time, trainer_booking_id=None):
        from gym_booking_backend.domain.constants import ScheduleStatus
        from gym_booking_backend.infrastructure.models import ClassSchedule

        class_overlap = ClassSchedule.objects.filter(
            trainer=trainer,
            status__in=[ScheduleStatus.OPEN, ScheduleStatus.FULL],
        ).filter(
            Q(start_time__lt=end_time) & Q(end_time__gt=start_time)
        ).exists()

        trainer_query = TrainerBooking.objects.filter(trainer=trainer, status__in=ACTIVE_BOOKING_STATUSES).filter(
            Q(start_time__lt=end_time) & Q(end_time__gt=start_time)
        )
        if trainer_booking_id:
            trainer_query = trainer_query.exclude(id=trainer_booking_id)

        booking_date = start_time.date()
        pt_start = start_time.time()
        pt_end = end_time.time()
        pt_overlap = PTBooking.objects.filter(
            trainer=trainer,
            booking_date=booking_date,
            status=PTBookingStatus.CONFIRMED,
            start_time__lt=pt_end,
            end_time__gt=pt_start,
        ).exists()

        return class_overlap or trainer_query.exists() or pt_overlap

    def create_booking(self, user, schedule, booking_code, note=""):
        return Booking.objects.create(user=user, schedule=schedule, booking_code=booking_code, note=note)

    def count_user_bookings_in_week(self, user, start_dt, end_dt):
        class_count = Booking.objects.filter(
            user=user,
            status__in=ACTIVE_BOOKING_STATUSES + [BookingStatus.COMPLETED],
            schedule__start_time__gte=start_dt,
            schedule__start_time__lte=end_dt,
        ).count()
        trainer_count = TrainerBooking.objects.filter(
            user=user,
            status__in=ACTIVE_BOOKING_STATUSES + [BookingStatus.COMPLETED],
            start_time__gte=start_dt,
            start_time__lte=end_dt,
        ).count()
        return class_count + trainer_count

    def get_user_trainer_bookings(self, user):
        return TrainerBooking.objects.select_related("trainer", "user__profile").filter(user=user)

    def get_trainer_personal_bookings(self, trainer):
        return TrainerBooking.objects.select_related("trainer", "user__profile").filter(trainer=trainer)

    def get_trainer_booking_by_id(self, booking_id):
        return TrainerBooking.objects.select_related("trainer", "user__profile").filter(id=booking_id).first()

    def create_trainer_booking(self, user, trainer, booking_code, start_time, end_time, note=""):
        return TrainerBooking.objects.create(
            user=user,
            trainer=trainer,
            booking_code=booking_code,
            start_time=start_time,
            end_time=end_time,
            note=note,
        )

    def get_user_trainer_monthly_bookings(self, user):
        return TrainerMonthlyBooking.objects.select_related("trainer", "user__profile").filter(user=user)

    def get_trainer_monthly_bookings(self, trainer):
        return TrainerMonthlyBooking.objects.select_related("trainer", "user__profile").filter(trainer=trainer)

    def get_all_trainer_monthly_bookings(self):
        return TrainerMonthlyBooking.objects.select_related("trainer", "user__profile").all()

    def get_trainer_monthly_booking_by_id(self, booking_id):
        return TrainerMonthlyBooking.objects.select_related("trainer", "user__profile").filter(id=booking_id).first()

    def has_overlapping_monthly_booking(self, user, trainer, start_date, end_date, booking_id=None):
        query = TrainerMonthlyBooking.objects.filter(
            user=user,
            trainer=trainer,
            status__in=ACTIVE_BOOKING_STATUSES,
            start_date__lte=end_date,
            end_date__gte=start_date,
        )
        if booking_id:
            query = query.exclude(id=booking_id)
        return query.exists()

    def create_trainer_monthly_booking(
        self,
        user,
        trainer,
        booking_code,
        start_date,
        end_date,
        months,
        sessions_per_week,
        preferred_time=None,
        note="",
    ):
        return TrainerMonthlyBooking.objects.create(
            user=user,
            trainer=trainer,
            booking_code=booking_code,
            start_date=start_date,
            end_date=end_date,
            months=months,
            sessions_per_week=sessions_per_week,
            preferred_time=preferred_time,
            note=note,
        )


booking_repository = DjangoBookingRepository()
