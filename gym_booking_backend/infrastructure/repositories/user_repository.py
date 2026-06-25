from django.contrib.auth.models import User
from gym_booking_backend.application.interfaces.repositories.iuser_repository import IUserRepository


class DjangoUserRepository(IUserRepository):
    def get_user_by_id(self, user_id):
        return User.objects.filter(id=user_id).first()

    def get_user_by_username(self, username):
        return User.objects.filter(username=username).first()

    def create_user(self, username, email, password, first_name="", last_name=""):
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )


user_repository = DjangoUserRepository()
