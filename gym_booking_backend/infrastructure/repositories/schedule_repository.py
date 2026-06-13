from django.db.models import F, Q
from django.utils import timezone

from gym_booking_backend.domain.constants import ScheduleStatus
from gym_booking_backend.infrastructure.models import ClassSchedule


def get_schedule_by_id(schedule_id):
    return (
        ClassSchedule.objects.select_related("gym_class", "trainer", "room")
        .filter(id=schedule_id)
        .first()
    )


def get_available_schedules():
    return ClassSchedule.objects.select_related("gym_class", "trainer", "room").filter(
        status=ScheduleStatus.OPEN,
        start_time__gt=timezone.now(),
        current_participants__lt=F("max_participants"),
    )


def get_all_schedules():
    return ClassSchedule.objects.select_related("gym_class", "trainer", "room").all()


def get_schedules_by_date(date):
    return ClassSchedule.objects.select_related("gym_class", "trainer", "room").filter(
        start_time__date=date
    )


def get_schedules_by_trainer(trainer_id):
    return ClassSchedule.objects.select_related("gym_class", "trainer", "room").filter(
        trainer_id=trainer_id
    )


def get_schedules_with_available_slots():
    return ClassSchedule.objects.select_related("gym_class", "trainer", "room").filter(
        current_participants__lt=F("max_participants")
    )


def has_room_conflict(room, start_time, end_time, exclude_id=None):
    queryset = ClassSchedule.objects.filter(room=room).filter(
        Q(start_time__lt=end_time) & Q(end_time__gt=start_time)
    )
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)
    return queryset.exists()


def has_trainer_conflict(trainer, start_time, end_time, exclude_id=None):
    queryset = ClassSchedule.objects.filter(trainer=trainer).filter(
        Q(start_time__lt=end_time) & Q(end_time__gt=start_time)
    )
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)
    return queryset.exists()
