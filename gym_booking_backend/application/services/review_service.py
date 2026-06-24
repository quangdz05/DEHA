from gym_booking_backend.domain.exceptions import ReviewException
from gym_booking_backend.infrastructure.repositories import booking_repository, class_repository, review_repository, trainer_repository


class ReviewService:
    def __init__(self, review_repo, trainer_repo, class_repo, booking_repo):
        self.review_repo = review_repo
        self.trainer_repo = trainer_repo
        self.class_repo = class_repo
        self.booking_repo = booking_repo

    def create_review(self, user, trainer_id=None, gym_class_id=None, rating=None, comment=""):
        if rating is None or int(rating) < 1 or int(rating) > 5:
            raise ReviewException("Rating must be from 1 to 5.")
        if not trainer_id and not gym_class_id:
            raise ReviewException("You must review a trainer or a class.")
        if trainer_id and gym_class_id:
            raise ReviewException("Review only one target at a time.")

        trainer = None
        gym_class = None

        if trainer_id:
            trainer = self.trainer_repo.get_trainer_by_id(trainer_id)
            if not trainer:
                raise ReviewException("Trainer not found.")
            # Verified review check for Trainer
            if not self.booking_repo.has_completed_booking_for_trainer(user, trainer_id):
                raise ReviewException("You can only review a trainer if you have completed a class with them.")
            if self.review_repo.has_user_reviewed_trainer(user, trainer):
                raise ReviewException("You already reviewed this trainer.")

        if gym_class_id:
            gym_class = self.class_repo.get_class_by_id(gym_class_id)
            if not gym_class:
                raise ReviewException("Class not found.")
            # Verified review check for Class
            if not self.booking_repo.has_completed_booking_for_class(user, gym_class_id):
                raise ReviewException("You can only review a class if you have attended and completed it.")
            if self.review_repo.has_user_reviewed_class(user, gym_class):
                raise ReviewException("You already reviewed this class.")

        return self.review_repo.create_review(user, trainer, gym_class, int(rating), comment)

    def get_reviews_by_trainer(self, trainer_id):
        return self.review_repo.get_reviews_by_trainer(trainer_id)

    def get_reviews_by_class(self, gym_class_id):
        return self.review_repo.get_reviews_by_class(gym_class_id)


# Backward compatibility instance and delegates
_service = ReviewService(review_repository, trainer_repository, class_repository, booking_repository)
create_review = _service.create_review
get_reviews_by_trainer = _service.get_reviews_by_trainer
get_reviews_by_class = _service.get_reviews_by_class
