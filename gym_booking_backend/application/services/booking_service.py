from uuid import uuid4
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from gym_booking_backend.application.validators import booking_validator
from gym_booking_backend.domain.constants import BookingStatus, CommonStatus, ScheduleStatus
from gym_booking_backend.domain.exceptions import BookingException, GymException
from gym_booking_backend.infrastructure.repositories.booking_repository import booking_repository
from gym_booking_backend.infrastructure.repositories.schedule_repository import schedule_repository
from gym_booking_backend.application.interfaces.services.ibooking_service import IBookingService
from gym_booking_backend.domain.result import Result


def _generate_booking_code():
    return f"BK{timezone.now():%Y%m%d}{uuid4().hex[:8].upper()}"


def _add_months(start_date, months):
    year = start_date.year + (start_date.month - 1 + months) // 12
    month = (start_date.month - 1 + months) % 12 + 1
    day = min(start_date.day, 28)
    return start_date.replace(year=year, month=month, day=day)


class BookingService(IBookingService):
    @transaction.atomic
    def create_booking(self, user, schedule_id, note="") -> Result:
        from gym_booking_backend.infrastructure.models import ClassSchedule, Booking
        
        try:
            schedule = (
                ClassSchedule.objects.select_for_update()
                .select_related("gym_class", "trainer", "room")
                .filter(id=schedule_id)
                .first()
            )
            if not schedule:
                return Result.failure_result("Schedule not found.", status_code=404)

            booking_validator.validate_schedule_is_open(schedule)
            booking_validator.validate_schedule_not_started(schedule)
            booking_validator.validate_user_has_active_membership(user)
            booking_validator.validate_membership_category_access(user, schedule)
            booking_validator.validate_user_not_duplicate_booking(user, schedule)
            booking_validator.validate_user_not_overlap_booking(user, schedule)
            booking_validator.validate_weekly_booking_limit(user, schedule)

            is_full = schedule.current_participants >= schedule.max_participants

            if is_full:
                booking = Booking.objects.create(
                    user=user,
                    schedule=schedule,
                    booking_code=_generate_booking_code(),
                    note=note,
                    status=BookingStatus.WAITLIST
                )
                return Result.success_result(booking, "Added to waitlist", status_code=201)
            else:
                booking = booking_repository.create_booking(user, schedule, _generate_booking_code(), note)
                schedule.current_participants += 1
                if schedule.current_participants >= schedule.max_participants:
                    schedule.status = ScheduleStatus.FULL
                schedule.save(update_fields=["current_participants", "status", "updated_at"])
                return Result.success_result(booking, "Booking created successfully", status_code=201)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    @transaction.atomic
    def cancel_booking(self, user, booking_id, cancellation_reason="") -> Result:
        from gym_booking_backend.infrastructure.models import Booking, ClassSchedule
        
        try:
            booking = Booking.objects.filter(id=booking_id).first()
            if not booking or booking.user_id != user.id:
                return Result.failure_result("Booking not found.", status_code=404)
            if booking.status == BookingStatus.CANCELLED:
                return Result.failure_result("Booking was already cancelled.", status_code=400)

            schedule = ClassSchedule.objects.select_for_update().filter(id=booking.schedule_id).first()
            booking_validator.validate_schedule_not_started(schedule)

            was_active = booking.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]

            booking.status = BookingStatus.CANCELLED
            booking.cancelled_at = timezone.now()
            booking.cancellation_reason = cancellation_reason
            booking.save(update_fields=["status", "cancelled_at", "cancellation_reason"])

            if was_active:
                next_waitlist = Booking.objects.select_for_update().filter(
                    schedule=schedule,
                    status=BookingStatus.WAITLIST
                ).order_by("created_at", "id").first()
                
                if next_waitlist:
                    next_waitlist.status = BookingStatus.PENDING
                    next_waitlist.save(update_fields=["status"])
                else:
                    if schedule.current_participants > 0:
                        schedule.current_participants -= 1
                    if schedule.status == ScheduleStatus.FULL:
                        schedule.status = ScheduleStatus.OPEN
                    schedule.save(update_fields=["current_participants", "status", "updated_at"])
                    
            return Result.success_result(booking, "Booking cancelled successfully", status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def complete_booking(self, booking_id) -> Result:
        try:
            booking = booking_repository.get_booking_by_id(booking_id)
            if not booking:
                return Result.failure_result("Booking not found.", status_code=404)
            booking.status = BookingStatus.COMPLETED
            booking.save(update_fields=["status"])
            return Result.success_result(booking, status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def mark_no_show(self, booking_id) -> Result:
        try:
            booking = booking_repository.get_booking_by_id(booking_id)
            if not booking:
                return Result.failure_result("Booking not found.", status_code=404)
            booking.status = BookingStatus.NO_SHOW
            booking.save(update_fields=["status"])
            return Result.success_result(booking, status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def get_my_bookings(self, user) -> Result:
        bookings = booking_repository.get_user_bookings(user)
        return Result.success_result(bookings, status_code=200)

    @transaction.atomic
    def create_trainer_booking(self, user, trainer_id, start_time, end_time, note="") -> Result:
        from gym_booking_backend.infrastructure.models import Trainer

        try:
            trainer = Trainer.objects.select_for_update().filter(id=trainer_id, status=CommonStatus.ACTIVE).first()
            if not trainer:
                return Result.failure_result("Trainer not found or inactive.", status_code=404)

            if start_time >= end_time:
                return Result.failure_result("Start time must be before end time.", status_code=400)
            if start_time <= timezone.now():
                return Result.failure_result("Booking time has already started.", status_code=400)

            booking_validator.validate_user_has_active_membership(user)
            booking_validator.validate_weekly_booking_limit(user, start_time=start_time)

            if booking_repository.has_user_overlapping_time(user, start_time, end_time):
                return Result.failure_result("You already have another booking in this time range.", status_code=400)

            if booking_repository.has_trainer_overlapping_time(trainer, start_time, end_time):
                return Result.failure_result("Trainer is already scheduled during this time range.", status_code=400)

            booking = booking_repository.create_trainer_booking(
                user=user,
                trainer=trainer,
                booking_code=_generate_booking_code(),
                start_time=start_time,
                end_time=end_time,
                note=note,
            )
            return Result.success_result(booking, "Trainer booking created successfully", status_code=201)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    @transaction.atomic
    def cancel_trainer_booking(self, user, booking_id, cancellation_reason="") -> Result:
        try:
            booking = booking_repository.get_trainer_booking_by_id(booking_id)
            if not booking or booking.user_id != user.id:
                return Result.failure_result("Trainer booking not found.", status_code=404)
            if booking.status == BookingStatus.CANCELLED:
                return Result.failure_result("Booking was already cancelled.", status_code=400)
            if booking.start_time <= timezone.now():
                return Result.failure_result("Booking has already started.", status_code=400)

            booking.status = BookingStatus.CANCELLED
            booking.cancelled_at = timezone.now()
            booking.cancellation_reason = cancellation_reason
            booking.save(update_fields=["status", "cancelled_at", "cancellation_reason", "updated_at"])
            return Result.success_result(booking, "Trainer booking cancelled", status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def get_my_trainer_bookings(self, user) -> Result:
        bookings = booking_repository.get_user_trainer_bookings(user)
        return Result.success_result(bookings, status_code=200)

    def get_trainer_personal_bookings(self, user) -> Result:
        from gym_booking_backend.infrastructure.models import Trainer

        try:
            trainer = Trainer.objects.filter(user=user).first()
            if not trainer:
                return Result.failure_result("Trainer profile not linked to user.", status_code=404)
            bookings = booking_repository.get_trainer_personal_bookings(trainer)
            return Result.success_result(bookings, status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def update_trainer_booking_status(self, user, booking_id, new_status) -> Result:
        from gym_booking_backend.infrastructure.models import Trainer

        try:
            if new_status not in [BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.COMPLETED, BookingStatus.NO_SHOW]:
                return Result.failure_result("Invalid booking status.", status_code=400)

            trainer = Trainer.objects.filter(user=user).first()
            if not trainer:
                return Result.failure_result("Trainer profile not linked to user.", status_code=404)

            booking = booking_repository.get_trainer_booking_by_id(booking_id)
            if not booking or booking.trainer_id != trainer.id:
                return Result.failure_result("Trainer booking not found.", status_code=404)

            booking.status = new_status
            if new_status == BookingStatus.CANCELLED:
                booking.cancelled_at = timezone.now()
                update_fields = ["status", "cancelled_at", "updated_at"]
            else:
                update_fields = ["status", "updated_at"]
            booking.save(update_fields=update_fields)
            return Result.success_result(booking, status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    @transaction.atomic
    def create_trainer_monthly_booking(
        self,
        user,
        trainer_id,
        start_date,
        months=1,
        sessions_per_week=3,
        preferred_time=None,
        note="",
    ) -> Result:
        from gym_booking_backend.infrastructure.models import Trainer

        try:
            trainer = Trainer.objects.select_for_update().filter(id=trainer_id, status=CommonStatus.ACTIVE).first()
            if not trainer:
                return Result.failure_result("Trainer not found or inactive.", status_code=404)

            if start_date < timezone.localdate():
                return Result.failure_result("Start date must not be in the past.", status_code=400)

            months = int(months or 1)
            sessions_per_week = int(sessions_per_week or 3)
            if months < 1 or months > 12:
                return Result.failure_result("Monthly trainer booking must be between 1 and 12 months.", status_code=400)
            if sessions_per_week < 1 or sessions_per_week > 7:
                return Result.failure_result("Sessions per week must be between 1 and 7.", status_code=400)

            booking_validator.validate_user_has_active_membership(user)

            end_date = _add_months(start_date, months) - timedelta(days=1)
            if booking_repository.has_overlapping_monthly_booking(user, trainer, start_date, end_date):
                return Result.failure_result("You already have an active monthly booking with this trainer in this period.", status_code=400)

            booking = booking_repository.create_trainer_monthly_booking(
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
            return Result.success_result(booking, "Monthly trainer booking created", status_code=201)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    @transaction.atomic
    def cancel_trainer_monthly_booking(self, user, booking_id, cancellation_reason="") -> Result:
        try:
            booking = booking_repository.get_trainer_monthly_booking_by_id(booking_id)
            if not booking or booking.user_id != user.id:
                return Result.failure_result("Monthly trainer booking not found.", status_code=404)
            if booking.status == BookingStatus.CANCELLED:
                return Result.failure_result("Booking was already cancelled.", status_code=400)
            if booking.start_date <= timezone.localdate():
                return Result.failure_result("Monthly booking has already started.", status_code=400)

            booking.status = BookingStatus.CANCELLED
            booking.cancelled_at = timezone.now()
            booking.cancellation_reason = cancellation_reason
            booking.save(update_fields=["status", "cancelled_at", "cancellation_reason", "updated_at"])
            return Result.success_result(booking, "Monthly booking cancelled", status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def get_my_trainer_monthly_bookings(self, user) -> Result:
        bookings = booking_repository.get_user_trainer_monthly_bookings(user)
        return Result.success_result(bookings, status_code=200)

    def get_trainer_monthly_bookings(self, user) -> Result:
        from gym_booking_backend.infrastructure.models import Trainer

        try:
            trainer = Trainer.objects.filter(user=user).first()
            if not trainer:
                return Result.failure_result("Trainer profile not linked to user.", status_code=404)
            bookings = booking_repository.get_trainer_monthly_bookings(trainer)
            return Result.success_result(bookings, status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def update_trainer_monthly_booking_status(self, user, booking_id, new_status) -> Result:
        from gym_booking_backend.infrastructure.models import Trainer

        try:
            if new_status not in [BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
                return Result.failure_result("Invalid booking status.", status_code=400)

            trainer = Trainer.objects.filter(user=user).first()
            if not trainer:
                return Result.failure_result("Trainer profile not linked to user.", status_code=404)

            booking = booking_repository.get_trainer_monthly_booking_by_id(booking_id)
            if not booking or booking.trainer_id != trainer.id:
                return Result.failure_result("Monthly trainer booking not found.", status_code=404)

            booking.status = new_status
            if new_status == BookingStatus.CANCELLED:
                booking.cancelled_at = timezone.now()
                update_fields = ["status", "cancelled_at", "updated_at"]
            else:
                update_fields = ["status", "updated_at"]
            booking.save(update_fields=update_fields)
            return Result.success_result(booking, status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def get_all_trainer_monthly_bookings(self, user) -> Result:
        from gym_booking_backend.domain.constants import UserRole
        if not hasattr(user, "profile") or user.profile.role != UserRole.ADMIN:
            return Result.failure_result("Permission denied.", status_code=403)
        bookings = booking_repository.get_all_trainer_monthly_bookings()
        return Result.success_result(bookings, status_code=200)

    def update_admin_trainer_monthly_booking_status(self, booking_id, new_status) -> Result:
        try:
            if new_status not in [BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
                return Result.failure_result("Invalid booking status.", status_code=400)

            booking = booking_repository.get_trainer_monthly_booking_by_id(booking_id)
            if not booking:
                return Result.failure_result("Monthly trainer booking not found.", status_code=404)

            booking.status = new_status
            if new_status == BookingStatus.CANCELLED:
                booking.cancelled_at = timezone.now()
                update_fields = ["status", "cancelled_at", "updated_at"]
            else:
                update_fields = ["status", "updated_at"]
            booking.save(update_fields=update_fields)
            return Result.success_result(booking, status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)


booking_service = BookingService()
