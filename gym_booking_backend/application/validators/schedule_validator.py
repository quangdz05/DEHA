from gym_booking_backend.domain.exceptions import InvalidScheduleException, ScheduleFullException
from gym_booking_backend.infrastructure.repositories import schedule_repository


def validate_schedule_time(start_time, end_time):
    if not start_time or not end_time or start_time >= end_time:
        raise InvalidScheduleException("Start time must be before end time.")


def validate_room_capacity(room, max_participants):
    if max_participants > room.capacity:
        raise InvalidScheduleException("Max participants cannot exceed room capacity.")


def validate_schedule_capacity(current_participants, max_participants):
    if current_participants >= max_participants:
        raise ScheduleFullException("Schedule is full.")


def validate_no_room_conflict(room, start_time, end_time, exclude_id=None):
    if schedule_repository.has_room_conflict(room, start_time, end_time, exclude_id):
        raise InvalidScheduleException("Room already has another schedule in this time range.")


def validate_no_trainer_conflict(trainer, start_time, end_time, exclude_id=None):
    if schedule_repository.has_trainer_conflict(trainer, start_time, end_time, exclude_id):
        raise InvalidScheduleException("Trainer already has another schedule in this time range.")

