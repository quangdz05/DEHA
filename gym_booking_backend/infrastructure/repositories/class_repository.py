from gym_booking_backend.infrastructure.models import Category, GymClass


def get_all_categories():
    return Category.objects.all()


def get_all_classes():
    return GymClass.objects.select_related("category", "trainer").all()


def get_class_by_id(class_id):
    return GymClass.objects.select_related("category", "trainer").filter(id=class_id).first()


def get_classes_by_category(category_id):
    return get_all_classes().filter(category_id=category_id)


def get_classes_by_trainer(trainer_id):
    return get_all_classes().filter(trainer_id=trainer_id)

