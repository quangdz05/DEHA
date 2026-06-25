from abc import ABC, abstractmethod


class IReviewRepository(ABC):
    @abstractmethod
    def get_review_by_id(self, review_id):
        pass

    @abstractmethod
    def get_reviews_by_trainer(self, trainer_id):
        pass

    @abstractmethod
    def get_reviews_by_class(self, gym_class_id):
        pass

    @abstractmethod
    def has_user_reviewed_trainer(self, user, trainer):
        pass

    @abstractmethod
    def has_user_reviewed_class(self, user, gym_class):
        pass

    @abstractmethod
    def create_review(self, user, trainer=None, gym_class=None, rating=5, comment=""):
        pass
