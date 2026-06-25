from abc import ABC, abstractmethod
from gym_booking_backend.domain.result import Result


class IReviewService(ABC):
    @abstractmethod
    def create_review(self, user, trainer_id=None, gym_class_id=None, rating=None, comment="") -> Result:
        pass

    @abstractmethod
    def get_reviews_by_trainer(self, trainer_id) -> Result:
        pass

    @abstractmethod
    def get_reviews_by_class(self, gym_class_id) -> Result:
        pass
