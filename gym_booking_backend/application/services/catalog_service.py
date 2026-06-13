from gym_booking_backend.infrastructure.repositories import class_repository, trainer_repository


def get_trainers():
    return trainer_repository.get_active_trainers()


def get_trainer(trainer_id):
    return trainer_repository.get_trainer_by_id(trainer_id)


def get_categories():
    return class_repository.get_all_categories()


def get_classes(category_id=None, trainer_id=None):
    if category_id:
        return class_repository.get_classes_by_category(category_id)
    if trainer_id:
        return class_repository.get_classes_by_trainer(trainer_id)
    return class_repository.get_all_classes()


def get_class(class_id):
    return class_repository.get_class_by_id(class_id)

