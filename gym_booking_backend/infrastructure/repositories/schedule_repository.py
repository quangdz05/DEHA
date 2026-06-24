from django.db.models import F, Q
from django.utils import timezone
from gym_booking_backend.domain.constants import ScheduleStatus
from gym_booking_backend.application.interfaces import IScheduleRepository
from gym_booking_backend.infrastructure.models import ClassSchedule


class DjangoScheduleRepository(IScheduleRepository):
    def get_schedule_by_id(self, schedule_id, select_for_update=False):
        queryset = ClassSchedule.objects.select_related("gym_class", "trainer", "room")
        if select_for_update:
            queryset = queryset.select_for_update()
        return queryset.filter(id=schedule_id).first()

    def get_available_schedules(self):
        return ClassSchedule.objects.select_related("gym_class", "trainer", "room").filter(
            status=ScheduleStatus.OPEN,
            start_time__gt=timezone.now(),
            current_participants__lt=F("max_participants"),
        )

    def get_all_schedules(self):
        return ClassSchedule.objects.select_related("gym_class", "trainer", "room").all()

    def get_schedules_by_date(self, date):
        return ClassSchedule.objects.select_related("gym_class", "trainer", "room").filter(
            start_time__date=date
        )

    def get_schedules_by_trainer(self, trainer_id):
        return ClassSchedule.objects.select_related("gym_class", "trainer", "room").filter(
            trainer_id=trainer_id
        )

    def get_schedules_with_available_slots(self):
        return ClassSchedule.objects.select_related("gym_class", "trainer", "room").filter(
            current_participants__lt=F("max_participants")
        )

    def has_room_conflict(self, room, start_time, end_time, exclude_id=None):
        queryset = ClassSchedule.objects.filter(room=room).filter(
            Q(start_time__lt=end_time) & Q(end_time__gt=start_time)
        )
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.exists()

    def has_trainer_conflict(self, trainer, start_time, end_time, exclude_id=None):
        from gym_booking_backend.infrastructure.models import TrainerBooking, PTBooking
        from gym_booking_backend.domain.constants import BookingStatus, PTBookingStatus

        ACTIVE_BOOKING_STATUSES = [BookingStatus.PENDING, BookingStatus.CONFIRMED]
        ACTIVE_PT_STATUSES = [PTBookingStatus.PENDING, PTBookingStatus.CONFIRMED]

        # 1. ClassSchedule conflict
        cs_queryset = ClassSchedule.objects.filter(trainer=trainer).filter(
            Q(start_time__lt=end_time) & Q(end_time__gt=start_time)
        )
        if exclude_id:
            cs_queryset = cs_queryset.exclude(id=exclude_id)
        if cs_queryset.exists():
            return True

        # 2. TrainerBooking conflict
        tb_overlap = TrainerBooking.objects.filter(
            trainer=trainer,
            status__in=ACTIVE_BOOKING_STATUSES,
        ).filter(
            Q(start_time__lt=end_time) & Q(end_time__gt=start_time)
        ).exists()
        if tb_overlap:
            return True

        # 3. PTBooking conflict
        booking_date = start_time.date() if hasattr(start_time, 'date') else start_time
        pt_start_time = start_time.time() if hasattr(start_time, 'time') else start_time
        pt_end_time = end_time.time() if hasattr(end_time, 'time') else end_time

        pt_overlap = PTBooking.objects.filter(
            trainer=trainer,
            booking_date=booking_date,
            status__in=ACTIVE_PT_STATUSES,
            start_time__lt=pt_end_time,
            end_time__gt=pt_start_time,
        ).exists()
        return pt_overlap


# Backward compatibility exports
_instance = DjangoScheduleRepository()
get_schedule_by_id = _instance.get_schedule_by_id
get_available_schedules = _instance.get_available_schedules
get_all_schedules = _instance.get_all_schedules
get_schedules_by_date = _instance.get_schedules_by_date
get_schedules_by_trainer = _instance.get_schedules_by_trainer
get_schedules_with_available_slots = _instance.get_schedules_with_available_slots
has_room_conflict = _instance.has_room_conflict
has_trainer_conflict = _instance.has_trainer_conflict
