from uuid import uuid4
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from gym_booking_backend.application.validators import booking_validator
from gym_booking_backend.domain.constants import BookingStatus, CommonStatus, ScheduleStatus
from gym_booking_backend.domain.exceptions import BookingException, InvalidScheduleException
from gym_booking_backend.infrastructure.repositories import booking_repository, schedule_repository


def _generate_booking_code():
    return f"BK{timezone.now():%Y%m%d}{uuid4().hex[:8].upper()}"


def _add_months(start_date, months):
    year = start_date.year + (start_date.month - 1 + months) // 12
    month = (start_date.month - 1 + months) % 12 + 1
    day = min(start_date.day, 28)
    return start_date.replace(year=year, month=month, day=day)


@transaction.atomic
def create_booking(user, schedule_id, note=""):
    from gym_booking_backend.infrastructure.models import ClassSchedule, Booking
    
    # Pessimistic lock on the schedule to prevent overbooking
    schedule = (
        ClassSchedule.objects.select_for_update()
        .select_related("gym_class", "trainer", "room")
        .filter(id=schedule_id)
        .first()
    )
    if not schedule:
        raise InvalidScheduleException("Schedule not found.")

    booking_validator.validate_schedule_is_open(schedule)
    booking_validator.validate_schedule_not_started(schedule)
    booking_validator.validate_user_has_active_membership(user)
    booking_validator.validate_membership_category_access(user, schedule)
    booking_validator.validate_user_not_duplicate_booking(user, schedule)
    booking_validator.validate_user_not_overlap_booking(user, schedule)
    booking_validator.validate_weekly_booking_limit(user, schedule)

    # Check if schedule is full
    is_full = schedule.current_participants >= schedule.max_participants

    if is_full:
        # Create waitlisted booking (does not take a slot)
        booking = Booking.objects.create(
            user=user,
            schedule=schedule,
            booking_code=_generate_booking_code(),
            note=note,
            status=BookingStatus.WAITLIST
        )
        return booking
    else:
        booking = booking_repository.create_booking(user, schedule, _generate_booking_code(), note)
        schedule.current_participants += 1
        if schedule.current_participants >= schedule.max_participants:
            schedule.status = ScheduleStatus.FULL
        schedule.save(update_fields=["current_participants", "status", "updated_at"])
        return booking


@transaction.atomic
def cancel_booking(user, booking_id, cancellation_reason=""):
    from gym_booking_backend.infrastructure.models import Booking, ClassSchedule
    
    booking = Booking.objects.filter(id=booking_id).first()
    if not booking or booking.user_id != user.id:
        raise BookingException("Booking not found.")
    if booking.status == BookingStatus.CANCELLED:
        raise BookingException("Booking was already cancelled.")

    # Pessimistic lock on the schedule to safely decrement participants
    schedule = ClassSchedule.objects.select_for_update().filter(id=booking.schedule_id).first()
    booking_validator.validate_schedule_not_started(schedule)

    was_active = booking.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = timezone.now()
    booking.cancellation_reason = cancellation_reason
    booking.save(update_fields=["status", "cancelled_at", "cancellation_reason"])

    if was_active:
        # Find next waitlisted booking to promote
        next_waitlist = Booking.objects.filter(
            schedule=schedule,
            status=BookingStatus.WAITLIST
        ).order_by("booked_at", "id").first()
        
        if next_waitlist:
            next_waitlist.status = BookingStatus.PENDING
            next_waitlist.save(update_fields=["status"])
            # The slot is occupied by the promoted booking, so current_participants remains same.
        else:
            if schedule.current_participants > 0:
                schedule.current_participants -= 1
            if schedule.status == ScheduleStatus.FULL:
                schedule.status = ScheduleStatus.OPEN
            schedule.save(update_fields=["current_participants", "status", "updated_at"])
            
    return booking


def complete_booking(booking_id):
    booking = booking_repository.get_booking_by_id(booking_id)
    if not booking:
        raise BookingException("Booking not found.")
    booking.status = BookingStatus.COMPLETED
    booking.save(update_fields=["status"])
    return booking


def mark_no_show(booking_id):
    booking = booking_repository.get_booking_by_id(booking_id)
    if not booking:
        raise BookingException("Booking not found.")
    booking.status = BookingStatus.NO_SHOW
    booking.save(update_fields=["status"])
    return booking


def get_my_bookings(user):
    return booking_repository.get_user_bookings(user)


@transaction.atomic
def create_trainer_booking(user, trainer_id, start_time, end_time, note=""):
    from gym_booking_backend.infrastructure.models import Trainer

    trainer = Trainer.objects.select_for_update().filter(id=trainer_id, status=CommonStatus.ACTIVE).first()
    if not trainer:
        raise BookingException("Trainer not found or inactive.")

    if start_time >= end_time:
        raise BookingException("Start time must be before end time.")
    if start_time <= timezone.now():
        raise BookingException("Booking time has already started.")

    booking_validator.validate_user_has_active_membership(user)
    booking_validator.validate_weekly_booking_limit(user, start_time=start_time)

    if booking_repository.has_user_overlapping_time(user, start_time, end_time):
        raise BookingException("You already have another booking in this time range.")

    if booking_repository.has_trainer_overlapping_time(trainer, start_time, end_time):
        raise BookingException("Trainer is already scheduled during this time range.")

    return booking_repository.create_trainer_booking(
        user=user,
        trainer=trainer,
        booking_code=_generate_booking_code(),
        start_time=start_time,
        end_time=end_time,
        note=note,
    )


@transaction.atomic
def cancel_trainer_booking(user, booking_id, cancellation_reason=""):
    booking = booking_repository.get_trainer_booking_by_id(booking_id)
    if not booking or booking.user_id != user.id:
        raise BookingException("Trainer booking not found.")
    if booking.status == BookingStatus.CANCELLED:
        raise BookingException("Booking was already cancelled.")
    if booking.start_time <= timezone.now():
        raise BookingException("Booking has already started.")

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = timezone.now()
    booking.cancellation_reason = cancellation_reason
    booking.save(update_fields=["status", "cancelled_at", "cancellation_reason", "updated_at"])
    return booking


def get_my_trainer_bookings(user):
    return booking_repository.get_user_trainer_bookings(user)


def get_trainer_personal_bookings(user):
    from gym_booking_backend.infrastructure.models import Trainer

    trainer = Trainer.objects.filter(user=user).first()
    if not trainer:
        raise BookingException("Trainer profile not linked to user.")
    return booking_repository.get_trainer_personal_bookings(trainer)


def update_trainer_booking_status(user, booking_id, new_status):
    from gym_booking_backend.infrastructure.models import Trainer

    if new_status not in [BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.COMPLETED, BookingStatus.NO_SHOW]:
        raise BookingException("Invalid booking status.")

    trainer = Trainer.objects.filter(user=user).first()
    if not trainer:
        raise BookingException("Trainer profile not linked to user.")

    booking = booking_repository.get_trainer_booking_by_id(booking_id)
    if not booking or booking.trainer_id != trainer.id:
        raise BookingException("Trainer booking not found.")

    booking.status = new_status
    if new_status == BookingStatus.CANCELLED:
        booking.cancelled_at = timezone.now()
        update_fields = ["status", "cancelled_at", "updated_at"]
    else:
        update_fields = ["status", "updated_at"]
    booking.save(update_fields=update_fields)
    return booking


@transaction.atomic
def create_trainer_monthly_booking(
    user,
    trainer_id,
    start_date,
    months=1,
    sessions_per_week=3,
    preferred_time=None,
    note="",
):
    from gym_booking_backend.infrastructure.models import Trainer

    trainer = Trainer.objects.select_for_update().filter(id=trainer_id, status=CommonStatus.ACTIVE).first()
    if not trainer:
        raise BookingException("Trainer not found or inactive.")

    if start_date < timezone.localdate():
        raise BookingException("Start date must not be in the past.")

    months = int(months or 1)
    sessions_per_week = int(sessions_per_week or 3)
    if months < 1 or months > 12:
        raise BookingException("Monthly trainer booking must be between 1 and 12 months.")
    if sessions_per_week < 1 or sessions_per_week > 7:
        raise BookingException("Sessions per week must be between 1 and 7.")

    booking_validator.validate_user_has_active_membership(user)

    end_date = _add_months(start_date, months) - timedelta(days=1)
    if booking_repository.has_overlapping_monthly_booking(user, trainer, start_date, end_date):
        raise BookingException("You already have an active monthly booking with this trainer in this period.")

    return booking_repository.create_trainer_monthly_booking(
        user=user,
        trainer=trainer,
        booking_code=_generate_booking_code(),
        start_date=start_date,
        end_date=end_date,
        months=months,
        sessions_per_week=sessions_per_week,
        preferred_time=preferred_time,
        note=note,
    )


@transaction.atomic
def cancel_trainer_monthly_booking(user, booking_id, cancellation_reason=""):
    booking = booking_repository.get_trainer_monthly_booking_by_id(booking_id)
    if not booking or booking.user_id != user.id:
        raise BookingException("Monthly trainer booking not found.")
    if booking.status == BookingStatus.CANCELLED:
        raise BookingException("Booking was already cancelled.")
    if booking.start_date <= timezone.localdate():
        raise BookingException("Monthly booking has already started.")

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = timezone.now()
    booking.cancellation_reason = cancellation_reason
    booking.save(update_fields=["status", "cancelled_at", "cancellation_reason", "updated_at"])
    return booking


def get_my_trainer_monthly_bookings(user):
    return booking_repository.get_user_trainer_monthly_bookings(user)


def get_trainer_monthly_bookings(user):
    from gym_booking_backend.infrastructure.models import Trainer

    trainer = Trainer.objects.filter(user=user).first()
    if not trainer:
        raise BookingException("Trainer profile not linked to user.")
    return booking_repository.get_trainer_monthly_bookings(trainer)


def update_trainer_monthly_booking_status(user, booking_id, new_status):
    from gym_booking_backend.infrastructure.models import Trainer

    if new_status not in [BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
        raise BookingException("Invalid booking status.")

    trainer = Trainer.objects.filter(user=user).first()
    if not trainer:
        raise BookingException("Trainer profile not linked to user.")

    booking = booking_repository.get_trainer_monthly_booking_by_id(booking_id)
    if not booking or booking.trainer_id != trainer.id:
        raise BookingException("Monthly trainer booking not found.")

    booking.status = new_status
    if new_status == BookingStatus.CANCELLED:
        booking.cancelled_at = timezone.now()
        update_fields = ["status", "cancelled_at", "updated_at"]
    else:
        update_fields = ["status", "updated_at"]
    booking.save(update_fields=update_fields)
    return booking


def get_admin_trainer_monthly_bookings():
    return booking_repository.get_all_trainer_monthly_bookings()


def update_admin_trainer_monthly_booking_status(booking_id, new_status):
    if new_status not in [BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
        raise BookingException("Invalid booking status.")

    booking = booking_repository.get_trainer_monthly_booking_by_id(booking_id)
    if not booking:
        raise BookingException("Monthly trainer booking not found.")

    booking.status = new_status
    if new_status == BookingStatus.CANCELLED:
        booking.cancelled_at = timezone.now()
        update_fields = ["status", "cancelled_at", "updated_at"]
    else:
        update_fields = ["status", "updated_at"]
    booking.save(update_fields=update_fields)
    return booking
