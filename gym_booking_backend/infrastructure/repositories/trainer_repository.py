from gym_booking_backend.domain.constants import CommonStatus
from gym_booking_backend.infrastructure.models import Trainer
from gym_booking_backend.application.interfaces.repositories.itrainer_repository import ITrainerRepository


class DjangoTrainerRepository(ITrainerRepository):
    def get_all_trainers(self):
        return Trainer.objects.all()

    def get_active_trainers(self):
        return Trainer.objects.filter(status=CommonStatus.ACTIVE)

    def get_trainer_by_id(self, trainer_id):
        return Trainer.objects.filter(id=trainer_id).first()


trainer_repository = DjangoTrainerRepository()
