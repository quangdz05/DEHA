from gym_booking_backend.infrastructure.repositories.class_repository import class_repository
from gym_booking_backend.infrastructure.repositories.trainer_repository import trainer_repository
from gym_booking_backend.application.interfaces.services.icatalog_service import ICatalogService
from gym_booking_backend.domain.result import Result


class CatalogService(ICatalogService):
    def get_trainers(self) -> Result:
        trainers = trainer_repository.get_active_trainers()
        return Result.success_result(trainers, status_code=200)

    def get_trainer(self, trainer_id) -> Result:
        trainer = trainer_repository.get_trainer_by_id(trainer_id)
        if not trainer:
            return Result.failure_result("Trainer not found", status_code=404)
        return Result.success_result(trainer, status_code=200)

    def get_categories(self) -> Result:
        categories = class_repository.get_all_categories()
        return Result.success_result(categories, status_code=200)

    def get_classes(self, category_id=None, trainer_id=None) -> Result:
        if category_id:
            classes = class_repository.get_classes_by_category(category_id)
        elif trainer_id:
            classes = class_repository.get_classes_by_trainer(trainer_id)
        else:
            classes = class_repository.get_all_classes()
        return Result.success_result(classes, status_code=200)

    def get_class(self, class_id) -> Result:
        gym_class = class_repository.get_class_by_id(class_id)
        if not gym_class:
            return Result.failure_result("Class not found", status_code=404)
        return Result.success_result(gym_class, status_code=200)


catalog_service = CatalogService()
