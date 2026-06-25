from abc import ABC, abstractmethod


class IUserRepository(ABC):
    @abstractmethod
    def get_user_by_id(self, user_id):
        pass

    @abstractmethod
    def get_user_by_username(self, username):
        pass

    @abstractmethod
    def create_user(self, username, email, password, first_name="", last_name=""):
        pass
