from gym_booking_backend.infrastructure.repositories import class_repository, trainer_repository


class CatalogService:
    def __init__(self, class_repo, trainer_repo):
        self.class_repo = class_repo
        self.trainer_repo = trainer_repo

    def get_trainers(self):
        return self.trainer_repo.get_active_trainers()

    def get_trainer(self, trainer_id):
        return self.trainer_repo.get_trainer_by_id(trainer_id)

    def get_categories(self):
        return self.class_repo.get_all_categories()

    def get_classes(self, category_id=None, trainer_id=None):
        if category_id:
            return self.class_repo.get_classes_by_category(category_id)
        if trainer_id:
            return self.class_repo.get_classes_by_trainer(trainer_id)
        return self.class_repo.get_all_classes()

    def get_class(self, class_id):
        return self.class_repo.get_class_by_id(class_id)


# Backward compatibility instance and delegates
_service = CatalogService(class_repository, trainer_repository)
get_trainers = _service.get_trainers
get_trainer = _service.get_trainer
get_categories = _service.get_categories
get_classes = _service.get_classes
get_class = _service.get_class
