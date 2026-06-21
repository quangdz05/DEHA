import datetime
from datetime import timedelta

from django.utils import timezone

from gym_booking_backend.domain.constants import ScheduleStatus
from gym_booking_backend.domain.exceptions import (
    DuplicateBookingException,
    InvalidScheduleException,
    MembershipRequiredException,
    OverlapBookingException,
    ScheduleAlreadyStartedException,
    ScheduleFullException,
)
from gym_booking_backend.infrastructure.repositories import booking_repository, membership_repository


def validate_schedule_is_open(schedule):
    if schedule.status != ScheduleStatus.OPEN:
        raise InvalidScheduleException("Schedule is not open for booking.")


def validate_schedule_not_full(schedule):
    if schedule.current_participants >= schedule.max_participants:
        raise ScheduleFullException("Schedule is full.")


def validate_schedule_not_started(schedule):
    if schedule.start_time <= timezone.now():
        raise ScheduleAlreadyStartedException("Schedule has already started.")


def validate_user_has_active_membership(user):
    if not membership_repository.has_active_membership(user):
        raise MembershipRequiredException("You need an active membership to book a class.")


def validate_user_not_duplicate_booking(user, schedule):
    if booking_repository.has_duplicate_booking(user, schedule):
        raise DuplicateBookingException("You already booked this schedule.")


def validate_user_not_overlap_booking(user, schedule):
    if booking_repository.has_overlapping_booking(user, schedule):
        raise OverlapBookingException("You already have another booking in this time range.")


def validate_weekly_booking_limit(user, schedule=None, start_time=None):
    membership = membership_repository.get_active_membership(user)
    if not membership:
        raise MembershipRequiredException("You need an active membership to book a class.")

    limit = membership.package.max_bookings_per_week
    if not limit:
        return

    if schedule:
        base_dt = timezone.as_localtime(schedule.start_time)
    elif start_time:
        base_dt = timezone.as_localtime(start_time) if timezone.is_aware(start_time) else timezone.make_aware(start_time)
    else:
        base_dt = timezone.localtime()

    local_date = base_dt.date()
    monday_date = local_date - timedelta(days=local_date.weekday())

    week_start = timezone.make_aware(
        datetime.datetime.combine(monday_date, datetime.time.min),
        timezone.get_current_timezone()
    )
    week_end = timezone.make_aware(
        datetime.datetime.combine(monday_date + timedelta(days=6), datetime.time.max),
        timezone.get_current_timezone()
    )

    current_count = booking_repository.count_user_bookings_in_week(user, week_start, week_end)
    if current_count >= limit:
        raise MembershipRequiredException("Weekly booking limit for your membership package has been reached.")


def validate_membership_category_access(user, schedule):
    membership = membership_repository.get_active_membership(user)
    if not membership:
        raise MembershipRequiredException("You need an active membership to book a class.")
    
    package = membership.package
    if package.allowed_categories.exists():
        category = schedule.gym_class.category
        if not package.allowed_categories.filter(id=category.id).exists():
            raise MembershipRequiredException("Your membership package does not allow booking this class category.")
