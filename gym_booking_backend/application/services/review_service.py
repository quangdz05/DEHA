from gym_booking_backend.domain.exceptions import ReviewException
from gym_booking_backend.infrastructure.repositories import class_repository, review_repository, trainer_repository


def create_review(user, trainer_id=None, gym_class_id=None, rating=None, comment=""):
    if rating is None or int(rating) < 1 or int(rating) > 5:
        raise ReviewException("Rating must be from 1 to 5.")
    if not trainer_id and not gym_class_id:
        raise ReviewException("You must review a trainer or a class.")
    if trainer_id and gym_class_id:
        raise ReviewException("Review only one target at a time.")

    trainer = None
    gym_class = None
    from gym_booking_backend.infrastructure.models import Booking
    from gym_booking_backend.domain.constants import BookingStatus

    if trainer_id:
        trainer = trainer_repository.get_trainer_by_id(trainer_id)
        if not trainer:
            raise ReviewException("Trainer not found.")
        # Verified review check for Trainer
        has_completed_booking = Booking.objects.filter(
            user=user,
            status=BookingStatus.COMPLETED,
            schedule__trainer_id=trainer_id
        ).exists()
        if not has_completed_booking:
            raise ReviewException("You can only review a trainer if you have completed a class with them.")
            
        if review_repository.has_user_reviewed_trainer(user, trainer):
            raise ReviewException("You already reviewed this trainer.")

    if gym_class_id:
        gym_class = class_repository.get_class_by_id(gym_class_id)
        if not gym_class:
            raise ReviewException("Class not found.")
        # Verified review check for Class
        has_completed_booking = Booking.objects.filter(
            user=user,
            status=BookingStatus.COMPLETED,
            schedule__gym_class_id=gym_class_id
        ).exists()
        if not has_completed_booking:
            raise ReviewException("You can only review a class if you have attended and completed it.")
            
        if review_repository.has_user_reviewed_class(user, gym_class):
            raise ReviewException("You already reviewed this class.")

    return review_repository.create_review(user, trainer, gym_class, int(rating), comment)


def get_reviews_by_trainer(trainer_id):
    return review_repository.get_reviews_by_trainer(trainer_id)


def get_reviews_by_class(gym_class_id):
    return review_repository.get_reviews_by_class(gym_class_id)
