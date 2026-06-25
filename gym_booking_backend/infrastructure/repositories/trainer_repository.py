from gym_booking_backend.domain.constants import CommonStatus
from gym_booking_backend.infrastructure.models import Trainer
from gym_booking_backend.application.interfaces.repositories.itrainer_repository import ITrainerRepository


class DjangoTrainerRepository(ITrainerRepository):
    def get_all_trainers(self):
        return Trainer.objects.all()

    def get_active_trainers(self):
        return Trainer.objects.filter(status=CommonStatus.ACTIVE)

    def get_trainer_by_id(self, trainer_id, select_for_update=False):
        queryset = Trainer.objects.filter(id=trainer_id)
        if select_for_update:
            queryset = queryset.select_for_update()
        return queryset.first()

    def get_trainer_by_user(self, user):
        return Trainer.objects.filter(user=user).first()

    def create_trainer(self, user, name, email, phone="", specialty="General Trainer", experience_years=1):
        return Trainer.objects.create(
            user=user,
            name=name,
            email=email,
            phone=phone,
            specialty=specialty,
            experience_years=experience_years,
            status=CommonStatus.ACTIVE,
        )


trainer_repository = DjangoTrainerRepository()
