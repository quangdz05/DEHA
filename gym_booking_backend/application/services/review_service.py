from gym_booking_backend.domain.exceptions import GymException
from gym_booking_backend.infrastructure.repositories.class_repository import class_repository
from gym_booking_backend.infrastructure.repositories.review_repository import review_repository
from gym_booking_backend.infrastructure.repositories.trainer_repository import trainer_repository
from gym_booking_backend.infrastructure.repositories.booking_repository import booking_repository
from gym_booking_backend.application.interfaces.services.ireview_service import IReviewService
from gym_booking_backend.domain.result import Result


class ReviewService(IReviewService):
    def create_review(self, user, trainer_id=None, gym_class_id=None, rating=None, comment="") -> Result:
        try:
            if rating is None or int(rating) < 1 or int(rating) > 5:
                return Result.failure_result("Rating must be from 1 to 5.", status_code=400)
            if not trainer_id and not gym_class_id:
                return Result.failure_result("You must review a trainer or a class.", status_code=400)
            if trainer_id and gym_class_id:
                return Result.failure_result("Review only one target at a time.", status_code=400)

            trainer = None
            gym_class = None

            if trainer_id:
                trainer = trainer_repository.get_trainer_by_id(trainer_id)
                if not trainer:
                    return Result.failure_result("Trainer not found.", status_code=404)
                
                if not booking_repository.has_completed_booking_for_trainer(user, trainer_id):
                    return Result.failure_result("You can only review a trainer if you have completed a class with them.", status_code=400)
                    
                if review_repository.has_user_reviewed_trainer(user, trainer):
                    return Result.failure_result("You already reviewed this trainer.", status_code=400)

            if gym_class_id:
                gym_class = class_repository.get_class_by_id(gym_class_id)
                if not gym_class:
                    return Result.failure_result("Class not found.", status_code=404)
                
                if not booking_repository.has_completed_booking_for_class(user, gym_class_id):
                    return Result.failure_result("You can only review a class if you have attended and completed it.", status_code=400)
                    
                if review_repository.has_user_reviewed_class(user, gym_class):
                    return Result.failure_result("You already reviewed this class.", status_code=400)

            review = review_repository.create_review(user, trainer, gym_class, int(rating), comment)
            return Result.success_result(review, "Review submitted successfully", status_code=201)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def get_reviews_by_trainer(self, trainer_id) -> Result:
        reviews = review_repository.get_reviews_by_trainer(trainer_id)
        return Result.success_result(reviews, status_code=200)

    def get_reviews_by_class(self, gym_class_id) -> Result:
        reviews = review_repository.get_reviews_by_class(gym_class_id)
        return Result.success_result(reviews, status_code=200)


review_service = ReviewService()
