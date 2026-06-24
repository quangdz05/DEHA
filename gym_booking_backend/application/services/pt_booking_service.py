from datetime import timedelta, datetime
from uuid import uuid4
from django.db import transaction
from django.utils import timezone
from gym_booking_backend.domain.constants import UserPTPackageStatus, PTBookingStatus, WeekdayChoices
from gym_booking_backend.domain.exceptions import PTBookingException, MembershipRequiredException
from gym_booking_backend.infrastructure.repositories import membership_repository, pt_repository, trainer_repository


class PTBookingService:
    def __init__(self, pt_repo, membership_repo, trainer_repo):
        self.pt_repo = pt_repo
        self.membership_repo = membership_repo
        self.trainer_repo = trainer_repo

    def _generate_pt_booking_code(self):
        return f"PT{timezone.now():%Y%m%d}{uuid4().hex[:8].upper()}"

    def _get_session_dates(self, start_date, selected_weekdays, total_sessions, duration_days):
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

    def _parse_time(self, time_value):
        """Parse a string time value into a time object."""
        if isinstance(time_value, str):
            try:
                return datetime.strptime(time_value, "%H:%M").time()
            except ValueError:
                return datetime.strptime(time_value, "%H:%M:%S").time()
        return time_value

    def _parse_weekdays(self, selected_weekdays):
        """Parse selected weekdays into a list of integers."""
        if isinstance(selected_weekdays, list):
            return [int(w) for w in selected_weekdays]
        elif isinstance(selected_weekdays, str):
            return [int(w) for w in selected_weekdays.split(",") if w.strip() != ""]
        else:
            raise PTBookingException("Selected weekdays is invalid.")

    def preview_monthly_pt_bookings(self, user, package_id, trainer_id, start_date, selected_weekdays, start_time, end_time):
        """
        Preview the list of dates and identify any schedule conflicts before purchasing.
        """
        if not self.membership_repo.has_active_membership(user):
            raise MembershipRequiredException("You need an active gym membership to purchase a PT package.")

        package = self.pt_repo.get_pt_package_by_id(package_id)
        if not package or not package.is_active:
            raise PTBookingException("PT Package not found or is inactive.")

        trainer = self.trainer_repo.get_trainer_by_id(trainer_id)
        if not trainer:
            raise PTBookingException("Trainer not found.")
        if trainer.status != "active":
            raise PTBookingException("Trainer is inactive.")

        # Parse and validate times
        start_time = self._parse_time(start_time)
        end_time = self._parse_time(end_time)

        if start_time >= end_time:
            raise PTBookingException("Start time must be before end time.")

        # Parse weekdays
        selected_weekdays = self._parse_weekdays(selected_weekdays)

        if not selected_weekdays:
            raise PTBookingException("At least one weekday must be selected.")

        # 1. Check if user already has an active UserPTPackage
        if self.pt_repo.has_active_pt_package(user):
            raise PTBookingException("You already have an active PT package subscription.")

        # 2. Check if PT has schedules on these weekdays and times
        for wd in selected_weekdays:
            sched = self.pt_repo.get_trainer_schedule_for_weekday(trainer, wd)
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
        session_dates = self._get_session_dates(start_date, selected_weekdays, package.total_sessions, package.duration_days)
        if len(session_dates) < package.total_sessions:
            raise PTBookingException(
                f"Cannot schedule all {package.total_sessions} sessions within the package duration of {package.duration_days} days. "
                f"Only {len(session_dates)} sessions could be generated. Please select more weekdays or change start date."
            )

        # 3. Check conflicts for each session date
        previews = []
        for s_date in session_dates:
            trainer_conflict = self.pt_repo.has_trainer_pt_booking_conflict(trainer, s_date, start_time, end_time)
            user_conflict = self.pt_repo.has_user_pt_booking_conflict(user, s_date, start_time, end_time)

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
    def create_monthly_pt_bookings(self, user, package_id, trainer_id, start_date, selected_weekdays, start_time, end_time, note=""):
        """
        Validate, purchase, and automatically generate PTBookings for the entire month.
        """
        # Parse weekdays
        selected_weekdays_list = self._parse_weekdays(selected_weekdays)

        # Run previews to get all validation and checks
        previews = self.preview_monthly_pt_bookings(
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

        package = self.pt_repo.get_pt_package_by_id(package_id)
        trainer = self.trainer_repo.get_trainer_by_id(trainer_id)

        weekdays_list = selected_weekdays_list
        start_time = self._parse_time(start_time)
        end_time = self._parse_time(end_time)

        # Create the UserPTPackage
        end_date = start_date + timedelta(days=package.duration_days - 1)
        user_pt_package = self.pt_repo.create_user_pt_package(
            user=user,
            trainer=trainer,
            package=package,
            start_date=start_date,
            end_date=end_date,
            total_sessions=package.total_sessions,
            weekdays_list=weekdays_list,
            start_time=start_time,
            end_time=end_time,
        )

        # Create PTBookings
        bookings = []
        for preview in previews:
            booking = self.pt_repo.create_pt_booking(
                user=user,
                trainer=trainer,
                user_pt_package=user_pt_package,
                booking_code=self._generate_pt_booking_code(),
                booking_date=preview["date"],
                start_time=start_time,
                end_time=end_time,
                status=PTBookingStatus.CONFIRMED,
                note=note,
            )
            bookings.append(booking)

        return user_pt_package, bookings

    def complete_pt_booking(self, booking_id):
        """
        Mark a PTBooking as completed.
        Updates the session count on the UserPTPackage.
        """
        with transaction.atomic():
            booking = self.pt_repo.get_pt_booking_by_id(booking_id, select_for_update=True)
            if not booking:
                raise PTBookingException("Booking not found.")
            if booking.status != PTBookingStatus.CONFIRMED:
                raise PTBookingException("Only confirmed bookings can be completed.")

            booking.status = PTBookingStatus.COMPLETED
            booking.save(update_fields=["status"])

            user_package = self.pt_repo.get_user_pt_package_by_id(booking.user_pt_package_id, select_for_update=True)
            if user_package:
                user_package.used_sessions += 1
                # remaining_sessions is a @property, no need to save
                if user_package.remaining_sessions == 0:
                    user_package.status = UserPTPackageStatus.COMPLETED
                user_package.save(update_fields=["used_sessions", "status"])

        return booking

    def cancel_pt_booking(self, booking_id):
        """
        Cancel a single PTBooking session.
        """
        with transaction.atomic():
            booking = self.pt_repo.get_pt_booking_by_id(booking_id, select_for_update=True)
            if not booking:
                raise PTBookingException("Booking not found.")
            if booking.status == PTBookingStatus.CANCELLED:
                raise PTBookingException("Booking is already cancelled.")

            was_completed = booking.status == PTBookingStatus.COMPLETED
            booking.status = PTBookingStatus.CANCELLED
            booking.save(update_fields=["status"])

            # Adjust counters if it was completed earlier
            if was_completed:
                user_package = self.pt_repo.get_user_pt_package_by_id(booking.user_pt_package_id, select_for_update=True)
                if user_package:
                    user_package.used_sessions = max(0, user_package.used_sessions - 1)
                    # remaining_sessions is a @property, no need to save
                    if user_package.status == UserPTPackageStatus.COMPLETED:
                        user_package.status = UserPTPackageStatus.ACTIVE
                    user_package.save(update_fields=["used_sessions", "status"])

        return booking

    def cancel_user_pt_package(self, user_pt_package_id):
        """
        Cancel the entire PT Package and all its pending or confirmed bookings.
        """
        with transaction.atomic():
            user_package = self.pt_repo.get_user_pt_package_by_id(user_pt_package_id, select_for_update=True)
            if not user_package:
                raise PTBookingException("PT Package subscription not found.")
            if user_package.status == UserPTPackageStatus.CANCELLED:
                raise PTBookingException("PT Package is already cancelled.")

            user_package.status = UserPTPackageStatus.CANCELLED
            user_package.save(update_fields=["status"])

            # Cancel all active bookings
            self.pt_repo.cancel_active_bookings_for_package(user_package)

        return user_package


# Backward compatibility instance and delegates
_service = PTBookingService(pt_repository, membership_repository, trainer_repository)

# Module-level functions for backward compatibility
get_session_dates = _service._get_session_dates
preview_monthly_pt_bookings = _service.preview_monthly_pt_bookings
create_monthly_pt_bookings = _service.create_monthly_pt_bookings
complete_pt_booking = _service.complete_pt_booking
cancel_pt_booking = _service.cancel_pt_booking
cancel_user_pt_package = _service.cancel_user_pt_package
