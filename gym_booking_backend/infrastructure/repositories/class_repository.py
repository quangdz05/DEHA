from gym_booking_backend.infrastructure.models import Category, GymClass
from gym_booking_backend.application.interfaces.repositories.iclass_repository import IClassRepository


class DjangoClassRepository(IClassRepository):
    def get_all_categories(self):
        return Category.objects.all()

    def get_all_classes(self):
        return GymClass.objects.select_related("category", "trainer").all()

    def get_class_by_id(self, class_id):
        return GymClass.objects.select_related("category", "trainer").filter(id=class_id).first()

    def get_classes_by_category(self, category_id):
        return self.get_all_classes().filter(category_id=category_id)

    def get_classes_by_trainer(self, trainer_id):
        return self.get_all_classes().filter(trainer_id=trainer_id)


class_repository = DjangoClassRepository()
