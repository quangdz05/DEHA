from abc import ABC, abstractmethod
from gym_booking_backend.domain.result import Result


class ICatalogService(ABC):
    @abstractmethod
    def get_trainers(self) -> Result:
        pass

    @abstractmethod
    def get_trainer(self, trainer_id) -> Result:
        pass

    @abstractmethod
    def get_categories(self) -> Result:
        pass

    @abstractmethod
    def get_classes(self, category_id=None, trainer_id=None) -> Result:
        pass

    @abstractmethod
    def get_class(self, class_id) -> Result:
        pass
