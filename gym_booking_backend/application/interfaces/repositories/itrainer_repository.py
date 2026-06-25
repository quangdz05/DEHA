from abc import ABC, abstractmethod


class ITrainerRepository(ABC):
    @abstractmethod
    def get_all_trainers(self):
        pass

    @abstractmethod
    def get_active_trainers(self):
        pass

    @abstractmethod
    def get_trainer_by_id(self, trainer_id):
        pass
