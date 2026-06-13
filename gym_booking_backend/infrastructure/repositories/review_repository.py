from gym_booking_backend.infrastructure.models import Review


def get_review_by_id(review_id):
    return Review.objects.filter(id=review_id).first()


def get_reviews_by_trainer(trainer_id):
    return Review.objects.select_related("user", "trainer").filter(trainer_id=trainer_id)


def get_reviews_by_class(gym_class_id):
    return Review.objects.select_related("user", "gym_class").filter(gym_class_id=gym_class_id)


def has_user_reviewed_trainer(user, trainer):
    return Review.objects.filter(user=user, trainer=trainer).exists()


def has_user_reviewed_class(user, gym_class):
    return Review.objects.filter(user=user, gym_class=gym_class).exists()


def create_review(user, trainer=None, gym_class=None, rating=5, comment=""):
    return Review.objects.create(user=user, trainer=trainer, gym_class=gym_class, rating=rating, comment=comment)
