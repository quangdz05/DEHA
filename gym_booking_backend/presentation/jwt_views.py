from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import User
from django.conf import settings

from gym_booking_backend.domain.exceptions import GymException

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

class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        username = request.data.get("username", "")
        password = request.data.get("password", "")

        user = authenticate(username=username, password=password)
        if user is None:
            return Response({"message": "Tên đăng nhập hoặc mật khẩu không đúng."}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response({
                "requires_2fa": True,
                "user_id": user.id
            }, status=status.HTTP_200_OK)

        # If staff/superuser, force role to admin
        from gym_booking_backend.domain.constants import UserRole
        if (user.is_superuser or user.is_staff) and profile.role != UserRole.ADMIN:
            profile.role = UserRole.ADMIN
            profile.save(update_fields=["role"])

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": profile.role,
            "full_name": profile.full_name,
            "access": access_token
        }, status=status.HTTP_200_OK)
        
        set_refresh_cookie(response, refresh_token)
        return response

class TokenRefreshAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"detail": "Refresh token missing."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh.payload.get("user_id")
            user = User.objects.get(id=user_id)
            profile = getattr(user, "profile", None)
            access_token = str(refresh.access_token)
        except (TokenError, InvalidToken, User.DoesNotExist) as e:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response({
            "access": access_token,
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": profile.role if profile else "member",
            "full_name": profile.full_name if profile else user.username,
        }, status=status.HTTP_200_OK)
        
        return response

class LogoutAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        response = Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
        response.delete_cookie("refresh_token", path="/api/auth/refresh/")
        return response
