from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, transaction

from gym_booking_backend.domain.exceptions import GymException
from gym_booking_backend.infrastructure.repositories import profile_repository, user_repository, trainer_repository


class AuthService:
    def __init__(self, user_repo, profile_repo, trainer_repo):
        self.user_repo = user_repo
        self.profile_repo = profile_repo
        self.trainer_repo = trainer_repo

    @transaction.atomic
    def register_user(self, username, email, password, first_name="", last_name="", role="member"):
        if self.user_repo.get_user_by_username(username):
            raise GymException("Username already exists.")
        try:
            with transaction.atomic():
                user = self.user_repo.create_user(username, email, password, first_name, last_name)
                if role == "admin":
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()
                full_name = f"{first_name} {last_name}".strip() or username
                self.profile_repo.update_profile(user, full_name=full_name, role=role)
                if role == "trainer":
                    self.trainer_repo.create_trainer(
                        user=user,
                        name=full_name,
                        email=email,
                    )
                return user
        except IntegrityError as exc:
            raise GymException("Could not register user with the provided data.") from exc

    def login_user(self, request, username, password):
        user = authenticate(request, username=username, password=password)
        if user is None:
            raise GymException("Ten dang nhap hoac mat khau khong dung.")
        login(request, user)
        return user

    def logout_user(self, request):
        logout(request)


# Backward compatibility instance and delegates
_service = AuthService(user_repository, profile_repository, trainer_repository)
register_user = _service.register_user
login_user = _service.login_user
logout_user = _service.logout_user
