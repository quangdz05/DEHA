from abc import ABC, abstractmethod


class IClassRepository(ABC):
    @abstractmethod
    def get_all_categories(self):
        pass

    @abstractmethod
    def get_all_classes(self):
        pass

    @abstractmethod
    def get_class_by_id(self, class_id):
        pass

    @abstractmethod
    def get_classes_by_category(self, category_id):
        pass

    @abstractmethod
    def get_classes_by_trainer(self, trainer_id):
        pass
