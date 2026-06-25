from abc import ABC, abstractmethod


class ITrainerRepository(ABC):
    @abstractmethod
    def get_all_trainers(self):
        pass

    @abstractmethod
    def get_active_trainers(self):
        pass

    @abstractmethod
    def get_trainer_by_id(self, trainer_id, select_for_update=False):
        pass

    @abstractmethod
    def get_trainer_by_user(self, user):
        pass

    @abstractmethod
    def create_trainer(self, user, name, email, phone="", specialty="General Trainer", experience_years=1):
        pass
