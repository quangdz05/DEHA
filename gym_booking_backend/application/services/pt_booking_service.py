from datetime import timedelta, datetime, time
from uuid import uuid4
from django.db import transaction
from django.utils import timezone
from gym_booking_backend.domain.constants import UserPTPackageStatus, PTBookingStatus, WeekdayChoices
from gym_booking_backend.domain.exceptions import PTBookingException, MembershipRequiredException
from gym_booking_backend.infrastructure.repositories import membership_repository, pt_repository
from gym_booking_backend.infrastructure.models import UserPTPackage, PTBooking, Trainer


def _generate_pt_booking_code():
    return f"PT{timezone.now():%Y%m%d}{uuid4().hex[:8].upper()}"


def get_session_dates(start_date, selected_weekdays, total_sessions, duration_days):
    """
    Generate the list of dates for the PT sessions.
    """
    end_date = start_date + timedelta(days=duration_days - 1)
    session_dates = []
    current_date = start_date

    while current_date <= end_date and len(session_dates) < total_sessions:
        if current_date.weekday() in selected_weekdays:
            session_dates.append(current_date)
        current_date += timedelta(days=1)

    return session_dates


def preview_monthly_pt_bookings(user, package_id, trainer_id, start_date, selected_weekdays, start_time, end_time):
    """
    Preview the list of dates and identify any schedule conflicts before purchasing.
    """
    if not membership_repository.has_active_membership(user):
        raise MembershipRequiredException("You need an active gym membership to purchase a PT package.")

    package = pt_repository.get_pt_package_by_id(package_id)
    if not package or not package.is_active:
        raise PTBookingException("PT Package not found or is inactive.")

    try:
        trainer = Trainer.objects.get(id=trainer_id)
    except Trainer.DoesNotExist:
        raise PTBookingException("Trainer not found.")

    if trainer.status != "active":
        raise PTBookingException("Trainer is inactive.")

    # Parse and validate times
    if isinstance(start_time, str):
        try:
            start_time = datetime.strptime(start_time, "%H:%M").time()
        except ValueError:
            start_time = datetime.strptime(start_time, "%H:%M:%S").time()

    if isinstance(end_time, str):
        try:
            end_time = datetime.strptime(end_time, "%H:%M").time()
        except ValueError:
            end_time = datetime.strptime(end_time, "%H:%M:%S").time()

    if start_time >= end_time:
        raise PTBookingException("Start time must be before end time.")

    # VĐ #4: selected_weekdays là JSONField, đã là list sẵn
    if isinstance(selected_weekdays, list):
        selected_weekdays = [int(w) for w in selected_weekdays]
    elif isinstance(selected_weekdays, str):
        selected_weekdays = [int(w) for w in selected_weekdays.split(",") if w.strip() != ""]
    else:
        raise PTBookingException("Selected weekdays is invalid.")

    if not selected_weekdays:
        raise PTBookingException("At least one weekday must be selected.")

    # 1. Check if user already has an active UserPTPackage
    active_packages = UserPTPackage.objects.filter(user=user, status=UserPTPackageStatus.ACTIVE)
    if active_packages.exists():
        raise PTBookingException("You already have an active PT package subscription.")

    # 2. Check if PT has schedules on these weekdays and times
    for wd in selected_weekdays:
        sched = pt_repository.get_trainer_schedule_for_weekday(trainer, wd)
        if not sched:
            weekday_label = dict(WeekdayChoices.choices).get(wd, str(wd))
            raise PTBookingException(f"Trainer {trainer.name} is not available on {weekday_label}.")

        # Check time bounds
        if start_time < sched.start_time or end_time > sched.end_time:
            raise PTBookingException(
                f"Requested time {start_time:%H:%M} - {end_time:%H:%M} is outside trainer's working hours "
                f"({sched.start_time:%H:%M} - {sched.end_time:%H:%M}) on {dict(WeekdayChoices.choices).get(wd)}."
            )

    # Generate dates
    session_dates = get_session_dates(start_date, selected_weekdays, package.total_sessions, package.duration_days)
    if len(session_dates) < package.total_sessions:
        raise PTBookingException(
            f"Cannot schedule all {package.total_sessions} sessions within the package duration of {package.duration_days} days. "
            f"Only {len(session_dates)} sessions could be generated. Please select more weekdays or change start date."
        )

    # 3. Check conflicts for each session date
    previews = []
    for s_date in session_dates:
        trainer_conflict = pt_repository.has_trainer_pt_booking_conflict(trainer, s_date, start_time, end_time)
        user_conflict = pt_repository.has_user_pt_booking_conflict(user, s_date, start_time, end_time)

        previews.append({
            "date": s_date,
            "start_time": start_time,
            "end_time": end_time,
            "trainer_conflict": trainer_conflict,
            "user_conflict": user_conflict,
            "is_valid": not (trainer_conflict or user_conflict)
        })

    return previews


@transaction.atomic
def create_monthly_pt_bookings(user, package_id, trainer_id, start_date, selected_weekdays, start_time, end_time, note=""):
    """
    Validate, purchase, and automatically generate PTBookings for the entire month.
    """
    # VĐ #4: selected_weekdays là JSONField, đã là list sẵn
    if isinstance(selected_weekdays, list):
        selected_weekdays_list = [int(wd) for wd in selected_weekdays]
    elif isinstance(selected_weekdays, str):
        selected_weekdays_list = [int(w) for w in selected_weekdays.split(",") if w.strip() != ""]
    else:
        raise PTBookingException("Selected weekdays is invalid.")

    # Run previews to get all validation and checks
    previews = preview_monthly_pt_bookings(
        user, package_id, trainer_id, start_date, selected_weekdays_list, start_time, end_time
    )

    # Check if any preview date is invalid
    conflicts = []
    for preview in previews:
        if not preview["is_valid"]:
            err = f"Date {preview['date']:%Y-%m-%d}: "
            if preview["trainer_conflict"]:
                err += "Trainer has another booking. "
            if preview["user_conflict"]:
                err += "You have another booking. "
            conflicts.append(err)

    if conflicts:
        raise PTBookingException("Schedule conflict detected: " + "; ".join(conflicts))

    package = pt_repository.get_pt_package_by_id(package_id)
    trainer = Trainer.objects.get(id=trainer_id)

    # VĐ #4: Lưu trực tiếp dưới dạng list (JSONField)
    weekdays_list = selected_weekdays_list

    if isinstance(start_time, str):
        try:
            start_time = datetime.strptime(start_time, "%H:%M").time()
        except ValueError:
            start_time = datetime.strptime(start_time, "%H:%M:%S").time()

    if isinstance(end_time, str):
        try:
            end_time = datetime.strptime(end_time, "%H:%M").time()
        except ValueError:
            end_time = datetime.strptime(end_time, "%H:%M:%S").time()

    # Create the UserPTPackage
    end_date = start_date + timedelta(days=package.duration_days - 1)
    user_pt_package = UserPTPackage.objects.create(
        user=user,
        trainer=trainer,
        package=package,
        start_date=start_date,
        end_date=end_date,
        total_sessions=package.total_sessions,
        used_sessions=0,
        status=UserPTPackageStatus.ACTIVE,
        selected_weekdays=weekdays_list,
        start_time=start_time,
        end_time=end_time,
    )

    # Create PTBookings
    bookings = []
    for preview in previews:
        booking = PTBooking.objects.create(
            user=user,
            trainer=trainer,
            user_pt_package=user_pt_package,
            booking_code=_generate_pt_booking_code(),
            booking_date=preview["date"],
            start_time=start_time,
            end_time=end_time,
            status=PTBookingStatus.CONFIRMED,
            note=note,
        )
        bookings.append(booking)

    return user_pt_package, bookings


def complete_pt_booking(booking_id):
    """
    Mark a PTBooking as completed.
    Updates the session count on the UserPTPackage.
    """
    with transaction.atomic():
        booking = PTBooking.objects.select_for_update().filter(id=booking_id).first()
        if not booking:
            raise PTBookingException("Booking not found.")
        if booking.status != PTBookingStatus.CONFIRMED:
            raise PTBookingException("Only confirmed bookings can be completed.")

        booking.status = PTBookingStatus.COMPLETED
        booking.save(update_fields=["status"])

        user_package = UserPTPackage.objects.select_for_update().filter(id=booking.user_pt_package_id).first()
        if user_package:
            user_package.used_sessions += 1
            # VĐ #14: remaining_sessions là @property, không cần save
            if user_package.remaining_sessions == 0:
                user_package.status = UserPTPackageStatus.COMPLETED
            user_package.save(update_fields=["used_sessions", "status"])

    return booking


def cancel_pt_booking(booking_id):
    """
    Cancel a single PTBooking session.
    """
    with transaction.atomic():
        booking = PTBooking.objects.select_for_update().filter(id=booking_id).first()
        if not booking:
            raise PTBookingException("Booking not found.")
        if booking.status == PTBookingStatus.CANCELLED:
            raise PTBookingException("Booking is already cancelled.")

        was_completed = booking.status == PTBookingStatus.COMPLETED
        booking.status = PTBookingStatus.CANCELLED
        booking.save(update_fields=["status"])

        # Adjust counters if it was completed earlier
        if was_completed:
            user_package = UserPTPackage.objects.select_for_update().filter(id=booking.user_pt_package_id).first()
            if user_package:
                user_package.used_sessions = max(0, user_package.used_sessions - 1)
                # VĐ #14: remaining_sessions là @property, không cần save
                if user_package.status == UserPTPackageStatus.COMPLETED:
                    user_package.status = UserPTPackageStatus.ACTIVE
                user_package.save(update_fields=["used_sessions", "status"])

    return booking


def cancel_user_pt_package(user_pt_package_id):
    """
    Cancel the entire PT Package and all its pending or confirmed bookings.
    """
    with transaction.atomic():
        user_package = UserPTPackage.objects.select_for_update().filter(id=user_pt_package_id).first()
        if not user_package:
            raise PTBookingException("PT Package subscription not found.")
        if user_package.status == UserPTPackageStatus.CANCELLED:
            raise PTBookingException("PT Package is already cancelled.")

        user_package.status = UserPTPackageStatus.CANCELLED
        user_package.save(update_fields=["status"])

        # Cancel all active bookings
        PTBooking.objects.filter(
            user_pt_package=user_package,
            status__in=[PTBookingStatus.PENDING, PTBookingStatus.CONFIRMED]
        ).update(status=PTBookingStatus.CANCELLED)

    return user_package
