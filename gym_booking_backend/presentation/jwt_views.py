from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import User
from django.conf import settings

from gym_booking_backend.domain.result import Result
from gym_booking_backend.presentation.views import BaseAPIView


def set_refresh_cookie(response, refresh_token):
    # SameSite=Lax/Strict depending on environment, path is restricted to refresh endpoint
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production (HTTPS)
        samesite="Strict",
        path="/api/auth/refresh/"
    )


class LoginAPIView(BaseAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        username = request.data.get("username", "")
        password = request.data.get("password", "")

        user = authenticate(username=username, password=password)
        if user is None:
            return self.handle_result(Result.failure_result("Tên đăng nhập hoặc mật khẩu không đúng.", status_code=400))

        profile = getattr(user, "profile", None)
        # Ensure profile exists
        if not profile:
            from gym_booking_backend.infrastructure.models import Profile
            profile = Profile.objects.create(
                user=user,
                full_name=user.get_full_name() or user.username
            )

        # Check if 2FA is enabled
        if profile.two_factor_enabled:
            return self.handle_result(Result.success_result({
                "requires_2fa": True,
                "user_id": user.id
            }, status_code=200))

        # If staff/superuser, force role to admin
        from gym_booking_backend.domain.constants import UserRole
        if (user.is_superuser or user.is_staff) and profile.role != UserRole.ADMIN:
            profile.role = UserRole.ADMIN
            profile.save(update_fields=["role"])

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": profile.role,
            "full_name": profile.full_name,
            "two_factor_enabled": profile.two_factor_enabled,
            "access": access_token
        }
        # Sync with Django session
        django_login(request, user)

        response = self.handle_result(Result.success_result(data, status_code=200))
        set_refresh_cookie(response, refresh_token)
        return response


class TokenRefreshAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return self.handle_result(Result.failure_result("Refresh token missing.", status_code=401))

        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh.payload.get("user_id")
            user = User.objects.get(id=user_id)
            profile = getattr(user, "profile", None)
            access_token = str(refresh.access_token)
        except (TokenError, InvalidToken, User.DoesNotExist) as e:
            return self.handle_result(Result.failure_result("Invalid refresh token.", status_code=401))

        # Sync with Django session
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        django_login(request, user)

        data = {
            "access": access_token,
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": profile.role if profile else "member",
            "full_name": profile.full_name if profile else user.username,
            "two_factor_enabled": profile.two_factor_enabled if profile else False,
        }
        
        return self.handle_result(Result.success_result(data, status_code=200))


class LogoutAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        django_logout(request)
        response = self.handle_result(Result.success_result({"message": "Logged out successfully."}, status_code=200))
        response.delete_cookie("refresh_token", path="/api/auth/refresh/")
        return response
