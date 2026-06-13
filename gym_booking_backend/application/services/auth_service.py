from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, transaction

from gym_booking_backend.domain.exceptions import GymException
from gym_booking_backend.infrastructure.repositories import profile_repository, user_repository


def register_user(username, email, password, first_name="", last_name="", role="member"):
    if user_repository.get_user_by_username(username):
        raise GymException("Username already exists.")
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
                from gym_booking_backend.domain.constants import CommonStatus
                from gym_booking_backend.infrastructure.models import Trainer
                Trainer.objects.create(
                    user=user,
                    name=full_name,
                    email=email,
                    phone="",
                    specialty="General Trainer",
                    experience_years=1,
                    status=CommonStatus.ACTIVE
                )
            return user
    except IntegrityError as exc:
        raise GymException("Could not register user with the provided data.") from exc


def login_user(request, username, password):
    user = authenticate(request, username=username, password=password)
    if user is None:
        raise GymException("Ten dang nhap hoac mat khau khong dung.")
    login(request, user)
    return user


def logout_user(request):
    logout(request)
