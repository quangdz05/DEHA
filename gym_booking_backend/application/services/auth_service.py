from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, transaction

from gym_booking_backend.domain.exceptions import GymException
from gym_booking_backend.infrastructure.repositories.profile_repository import profile_repository
from gym_booking_backend.infrastructure.repositories.user_repository import user_repository
from gym_booking_backend.infrastructure.repositories.trainer_repository import trainer_repository
from gym_booking_backend.application.interfaces.services.iauth_service import IAuthService
from gym_booking_backend.domain.result import Result


class AuthService(IAuthService):
    def register_user(self, username, email, password, first_name="", last_name="", role="member") -> Result:
        if user_repository.get_user_by_username(username):
            return Result.failure_result("Username already exists.", status_code=400)
        if not email:
            return Result.failure_result("Email không được để trống.", status_code=400)
        email = email.strip()
        from django.contrib.auth.models import User
        if User.objects.filter(email=email).exists():
            return Result.failure_result("Email này đã được sử dụng bởi một tài khoản khác.", status_code=400)
        try:
            with transaction.atomic():
                user = user_repository.create_user(username, email, password, first_name, last_name)
                if role == "admin":
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()
                full_name = f"{first_name} {last_name}".strip() or username
                profile_repository.update_profile(user, full_name=full_name, role=role)
                if role == "trainer":
                    trainer_repository.create_trainer(
                        user=user,
                        name=full_name,
                        email=email,
                    )
                return Result.success_result(user, "User registered successfully", status_code=201)
        except IntegrityError as exc:
            return Result.failure_result("Could not register user with the provided data.", status_code=400)
        except GymException as exc:
            return Result.failure_result(str(exc), status_code=400)

    def login_user(self, request, username, password) -> Result:
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Result.failure_result("Ten dang nhap hoac mat khau khong dung.", status_code=400)
        login(request, user)
        return Result.success_result(user, "Logged in successfully", status_code=200)

    def logout_user(self, request) -> Result:
        logout(request)
        return Result.success_result(None, "Logged out successfully", status_code=200)


auth_service = AuthService()
