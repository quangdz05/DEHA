from abc import ABC, abstractmethod


class IProfileRepository(ABC):
    @abstractmethod
    def get_profile_by_user(self, user):
        pass

    @abstractmethod
    def update_profile(self, user, **data):
        pass
