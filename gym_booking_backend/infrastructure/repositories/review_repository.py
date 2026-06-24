from gym_booking_backend.application.interfaces import IReviewRepository
from gym_booking_backend.infrastructure.models import Review


class DjangoReviewRepository(IReviewRepository):
    def get_review_by_id(self, review_id):
        return Review.objects.filter(id=review_id).first()

    def get_reviews_by_trainer(self, trainer_id):
        return Review.objects.select_related("user", "trainer").filter(trainer_id=trainer_id)

    def get_reviews_by_class(self, gym_class_id):
        return Review.objects.select_related("user", "gym_class").filter(gym_class_id=gym_class_id)

    def has_user_reviewed_trainer(self, user, trainer):
        return Review.objects.filter(user=user, trainer=trainer).exists()

    def has_user_reviewed_class(self, user, gym_class):
        return Review.objects.filter(user=user, gym_class=gym_class).exists()

    def create_review(self, user, trainer=None, gym_class=None, rating=5, comment=""):
        return Review.objects.create(user=user, trainer=trainer, gym_class=gym_class, rating=rating, comment=comment)


# Backward compatibility exports
_instance = DjangoReviewRepository()
get_review_by_id = _instance.get_review_by_id
get_reviews_by_trainer = _instance.get_reviews_by_trainer
get_reviews_by_class = _instance.get_reviews_by_class
has_user_reviewed_trainer = _instance.has_user_reviewed_trainer
has_user_reviewed_class = _instance.has_user_reviewed_class
create_review = _instance.create_review
