from gym_booking_backend.application.services import review_service


def execute(user, trainer_id=None, gym_class_id=None, rating=None, comment=""):
    return review_service.create_review(user, trainer_id, gym_class_id, rating, comment)
