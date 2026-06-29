from datetime import timedelta, datetime
from uuid import uuid4
from django.db import transaction
from django.utils import timezone
from gym_booking_backend.domain.constants import UserPTPackageStatus, PTBookingStatus, WeekdayChoices
from gym_booking_backend.domain.exceptions import GymException
from gym_booking_backend.infrastructure.repositories.membership_repository import membership_repository
from gym_booking_backend.infrastructure.repositories.pt_repository import pt_repository
from gym_booking_backend.infrastructure.repositories.trainer_repository import trainer_repository
from gym_booking_backend.infrastructure.models import UserPTPackage, PTBooking, Trainer
from gym_booking_backend.application.interfaces.services.ipt_booking_service import IPTBookingService
from gym_booking_backend.domain.result import Result


def _generate_pt_booking_code():
    return f"PT{timezone.now():%Y%m%d}{uuid4().hex[:8].upper()}"


def get_session_dates(start_date, selected_weekdays, total_sessions, duration_days):
    end_date = start_date + timedelta(days=duration_days - 1)
    session_dates = []
    current_date = start_date

    while current_date <= end_date and len(session_dates) < total_sessions:
        if current_date.weekday() in selected_weekdays:
            session_dates.append(current_date)
        current_date += timedelta(days=1)

    return session_dates


def get_trainer_busy_slots(trainer, start_date, end_date):
    from gym_booking_backend.infrastructure.models import PTBooking, TrainerBooking
    
    ACTIVE_PT_STATUSES = ["pending", "confirmed"]
    ACTIVE_BOOKING_STATUSES = ["pending", "confirmed"]
    
    busy = []
    
    # 1. PTBooking
    pt_bookings = PTBooking.objects.filter(
        trainer=trainer,
        booking_date__range=[start_date, end_date],
        status__in=ACTIVE_PT_STATUSES
    ).order_by('booking_date', 'start_time')
    for b in pt_bookings:
        busy.append({
            "type": "pt_booking",
            "date": b.booking_date.strftime("%Y-%m-%d"),
            "start_time": b.start_time.strftime("%H:%M"),
            "end_time": b.end_time.strftime("%H:%M"),
            "description": f"Personal Training Booking ({b.start_time.strftime('%H:%M')} - {b.end_time.strftime('%H:%M')})"
        })
        
    # 2. TrainerBooking
    trainer_bookings = TrainerBooking.objects.filter(
        trainer=trainer,
        start_time__date__range=[start_date, end_date],
        status__in=ACTIVE_BOOKING_STATUSES
    ).order_by('start_time')
    for b in trainer_bookings:
        start_dt = b.start_time
        end_dt = b.end_time
        busy.append({
            "type": "trainer_booking",
            "date": start_dt.date().strftime("%Y-%m-%d"),
            "start_time": start_dt.time().strftime("%H:%M"),
            "end_time": end_dt.time().strftime("%H:%M"),
            "description": f"Trainer Booking ({start_dt.time().strftime('%H:%M')} - {end_dt.time().strftime('%H:%M')})"
        })
        
    busy.sort(key=lambda x: (x["date"], x["start_time"]))
    return busy


class PTBookingService(IPTBookingService):
    def preview_monthly_pt_bookings(self, user, months, trainer_id, start_date, selected_weekdays, start_time, end_time) -> Result:
        try:
            if not membership_repository.has_active_membership(user):
                return Result.failure_result("You need an active gym membership to purchase a PT package.", status_code=400)

            trainer = trainer_repository.get_trainer_by_id(trainer_id)
            if not trainer:
                return Result.failure_result("Trainer not found.", status_code=404)

            if trainer.status != "active":
                return Result.failure_result("Trainer is inactive.", status_code=400)

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
                return Result.failure_result("Start time must be before end time.", status_code=400)

            if isinstance(selected_weekdays, list):
                selected_weekdays = [int(w) for w in selected_weekdays]
            elif isinstance(selected_weekdays, str):
                selected_weekdays = [int(w) for w in selected_weekdays.split(",") if w.strip() != ""]
            else:
                return Result.failure_result("Selected weekdays is invalid.", status_code=400)

            if not selected_weekdays:
                return Result.failure_result("At least one weekday must be selected.", status_code=400)

            if pt_repository.has_active_pt_package(user):
                return Result.failure_result("You already have an active PT package subscription.", status_code=400)

            for wd in selected_weekdays:
                sched = pt_repository.get_trainer_schedule_for_weekday(trainer, wd)
                if not sched:
                    weekday_label = dict(WeekdayChoices.choices).get(wd, str(wd))
                    avail_schedules = pt_repository.get_trainer_schedules(trainer)
                    schedule_details = [
                        {
                            "weekday": dict(WeekdayChoices.choices).get(s.weekday, str(s.weekday)),
                            "weekday_code": s.weekday,
                            "start_time": s.start_time.strftime("%H:%M") if s.start_time else "",
                            "end_time": s.end_time.strftime("%H:%M") if s.end_time else "",
                        }
                        for s in avail_schedules
                    ]
                    busy_slots = get_trainer_busy_slots(trainer, start_date, start_date + timedelta(days=months * 30))
                    return Result(
                        success=False,
                        message=f"Trainer {trainer.name} is not available on {weekday_label}.",
                        data={
                            "trainer_schedule": schedule_details,
                            "busy_slots": busy_slots
                        },
                        status_code=400
                    )

                if start_time < sched.start_time or end_time > sched.end_time:
                    avail_schedules = pt_repository.get_trainer_schedules(trainer)
                    schedule_details = [
                        {
                            "weekday": dict(WeekdayChoices.choices).get(s.weekday, str(s.weekday)),
                            "weekday_code": s.weekday,
                            "start_time": s.start_time.strftime("%H:%M") if s.start_time else "",
                            "end_time": s.end_time.strftime("%H:%M") if s.end_time else "",
                        }
                        for s in avail_schedules
                    ]
                    busy_slots = get_trainer_busy_slots(trainer, start_date, start_date + timedelta(days=months * 30))
                    return Result(
                        success=False,
                        message=(
                            f"Requested time {start_time:%H:%M} - {end_time:%H:%M} is outside trainer's working hours "
                            f"({sched.start_time:%H:%M} - {sched.end_time:%H:%M}) on {dict(WeekdayChoices.choices).get(wd)}."
                        ),
                        data={
                            "trainer_schedule": schedule_details,
                            "busy_slots": busy_slots
                        },
                        status_code=400
                    )

            # Generate dynamic session dates based on start_date, selected weekdays and duration of months
            duration_days = months * 30
            end_date = start_date + timedelta(days=duration_days - 1)
            session_dates = []
            current_date = start_date

            while current_date <= end_date:
                if current_date.weekday() in selected_weekdays:
                    session_dates.append(current_date)
                current_date += timedelta(days=1)

            if not session_dates:
                return Result.failure_result(
                    "No sessions could be generated within the selected timeframe. Please select more weekdays or change start date.",
                    status_code=400
                )

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

            return Result.success_result(previews, status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    @transaction.atomic
    def create_monthly_pt_bookings(self, user, months, trainer_id, start_date, selected_weekdays, start_time, end_time, note="") -> Result:
        try:
            if isinstance(selected_weekdays, list):
                selected_weekdays_list = [int(wd) for wd in selected_weekdays]
            elif isinstance(selected_weekdays, str):
                selected_weekdays_list = [int(w) for w in selected_weekdays.split(",") if w.strip() != ""]
            else:
                return Result.failure_result("Selected weekdays is invalid.", status_code=400)

            preview_res = self.preview_monthly_pt_bookings(
                user, months, trainer_id, start_date, selected_weekdays_list, start_time, end_time
            )
            if not preview_res.success:
                return preview_res

            previews = preview_res.data
            
            trainer = trainer_repository.get_trainer_by_id(trainer_id)

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
                avail_schedules = pt_repository.get_trainer_schedules(trainer)
                schedule_details = [
                    {
                        "weekday": dict(WeekdayChoices.choices).get(s.weekday, str(s.weekday)),
                        "weekday_code": s.weekday,
                        "start_time": s.start_time.strftime("%H:%M") if s.start_time else "",
                        "end_time": s.end_time.strftime("%H:%M") if s.end_time else "",
                    }
                    for s in avail_schedules
                ]
                busy_slots = get_trainer_busy_slots(trainer, start_date, start_date + timedelta(days=months * 30))
                return Result(
                    success=False,
                    message="Schedule conflict detected: " + "; ".join(conflicts),
                    data={
                        "trainer_schedule": schedule_details,
                        "busy_slots": busy_slots
                    },
                    status_code=400
                )

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

            end_date = start_date + timedelta(days=months * 30 - 1)
            total_sessions = len(previews)
            user_pt_package = pt_repository.create_user_pt_package(
                user=user,
                trainer=trainer,
                start_date=start_date,
                end_date=end_date,
                total_sessions=total_sessions,
                weekdays_list=weekdays_list,
                start_time=start_time,
                end_time=end_time,
            )

            bookings = []
            for preview in previews:
                booking = pt_repository.create_pt_booking(
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

            return Result.success_result({"package": user_pt_package, "bookings": bookings}, "PT Bookings generated successfully", status_code=201)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def complete_pt_booking(self, booking_id) -> Result:
        try:
            with transaction.atomic():
                booking = pt_repository.get_pt_booking_by_id(booking_id, select_for_update=True)
                if not booking:
                    return Result.failure_result("Booking not found.", status_code=404)
                if booking.status != PTBookingStatus.CONFIRMED:
                    return Result.failure_result("Only confirmed bookings can be completed.", status_code=400)

                booking.status = PTBookingStatus.COMPLETED
                booking.save(update_fields=["status"])

                user_package = pt_repository.get_user_pt_package_by_id(booking.user_pt_package_id, select_for_update=True)
                if user_package:
                    from django.db.models import F
                    user_package.used_sessions = F("used_sessions") + 1
                    user_package.save(update_fields=["used_sessions"])
                    user_package.refresh_from_db()
                    if user_package.remaining_sessions == 0:
                        user_package.status = UserPTPackageStatus.COMPLETED
                        user_package.save(update_fields=["status"])

            return Result.success_result(booking, status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def cancel_pt_booking(self, booking_id) -> Result:
        try:
            with transaction.atomic():
                booking = pt_repository.get_pt_booking_by_id(booking_id, select_for_update=True)
                if not booking:
                    return Result.failure_result("Booking not found.", status_code=404)
                if booking.status == PTBookingStatus.CANCELLED:
                    return Result.failure_result("Booking is already cancelled.", status_code=400)

                was_completed = booking.status == PTBookingStatus.COMPLETED
                booking.status = PTBookingStatus.CANCELLED
                booking.save(update_fields=["status"])

                if was_completed:
                    user_package = pt_repository.get_user_pt_package_by_id(booking.user_pt_package_id, select_for_update=True)
                    if user_package:
                        user_package.used_sessions = max(0, user_package.used_sessions - 1)
                        if user_package.status == UserPTPackageStatus.COMPLETED:
                            user_package.status = UserPTPackageStatus.ACTIVE
                        user_package.save(update_fields=["used_sessions", "status"])

            return Result.success_result(booking, status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def cancel_user_pt_package(self, user_pt_package_id) -> Result:
        try:
            with transaction.atomic():
                user_package = pt_repository.get_user_pt_package_by_id(user_pt_package_id, select_for_update=True)
                if not user_package:
                    return Result.failure_result("PT Package subscription not found.", status_code=404)
                if user_package.status == UserPTPackageStatus.CANCELLED:
                    return Result.failure_result("PT Package is already cancelled.", status_code=400)

                user_package.status = UserPTPackageStatus.CANCELLED
                user_package.save(update_fields=["status"])

                pt_repository.cancel_active_bookings_for_package(user_package)

            return Result.success_result(user_package, status_code=200)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)


pt_booking_service = PTBookingService()
