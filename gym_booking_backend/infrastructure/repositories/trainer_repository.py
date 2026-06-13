from gym_booking_backend.domain.constants import CommonStatus
from gym_booking_backend.infrastructure.models import Trainer


def get_all_trainers():
    return Trainer.objects.all()


def get_active_trainers():
    return Trainer.objects.filter(status=CommonStatus.ACTIVE)


def get_trainer_by_id(trainer_id):
    return Trainer.objects.filter(id=trainer_id).first()

