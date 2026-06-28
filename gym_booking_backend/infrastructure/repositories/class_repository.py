from gym_booking_backend.application.interfaces.repositories.iclass_repository import IClassRepository


class DjangoClassRepository(IClassRepository):
    def get_all_categories(self):
        return []

    def get_all_classes(self):
        return []

    def get_class_by_id(self, class_id):
        return None

    def get_classes_by_category(self, category_id):
        return []

    def get_classes_by_trainer(self, trainer_id):
        return []


class_repository = DjangoClassRepository()
