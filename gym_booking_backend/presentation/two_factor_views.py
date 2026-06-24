import pyotp
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

from gym_booking_backend.presentation.jwt_views import set_refresh_cookie

class TwoFactorSetupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = getattr(request.user, "profile", None)
        if not profile:
            from gym_booking_backend.infrastructure.models import Profile
            profile = Profile.objects.create(user=request.user, full_name=request.user.username)

        if profile.two_factor_enabled:
            return Response({"message": "Tài khoản của bạn đã được bật 2FA trước đó."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate new base32 secret
        secret = pyotp.random_base32()
        profile.two_factor_secret = secret
        profile.save(update_fields=["two_factor_secret"])

        # Create provisioning URI for Authenticator apps
        totp = pyotp.TOTP(secret)
        email = request.user.email or request.user.username
        provisioning_uri = totp.provisioning_uri(name=email, issuer_name="GymBooking")

        return Response({
            "secret": secret,
            "provisioning_uri": provisioning_uri
        }, status=status.HTTP_200_OK)

class TwoFactorEnableAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get("code", "").strip()
        profile = getattr(request.user, "profile", None)

        if not profile or not profile.two_factor_secret:
            return Response({"message": "Vui lòng gọi API Setup trước để khởi tạo 2FA."}, status=status.HTTP_400_BAD_REQUEST)

        if profile.two_factor_enabled:
            return Response({"message": "Tài khoản của bạn đã bật 2FA rồi."}, status=status.HTTP_400_BAD_REQUEST)

        totp = pyotp.TOTP(profile.two_factor_secret)
        if totp.verify(code):
            profile.two_factor_enabled = True
            profile.save(update_fields=["two_factor_enabled"])
            return Response({"message": "Kích hoạt xác thực 2 lớp (2FA) thành công!"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Mã xác minh OTP không đúng hoặc đã hết hạn."}, status=status.HTTP_400_BAD_REQUEST)

class TwoFactorDisableAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get("code", "").strip()
        profile = getattr(request.user, "profile", None)

        if not profile or not profile.two_factor_enabled:
            return Response({"message": "Tài khoản của bạn chưa kích hoạt 2FA."}, status=status.HTTP_400_BAD_REQUEST)

        # Require verification to disable
        totp = pyotp.TOTP(profile.two_factor_secret)
        if totp.verify(code):
            profile.two_factor_enabled = False
            profile.two_factor_secret = ""
            profile.save(update_fields=["two_factor_enabled", "two_factor_secret"])
            return Response({"message": "Đã hủy kích hoạt xác thực 2 lớp (2FA)."}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Mã xác minh OTP không đúng hoặc đã hết hạn."}, status=status.HTTP_400_BAD_REQUEST)

class TwoFactorVerifyAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get("user_id")
        code = request.data.get("code", "").strip()

        if not user_id or not code:
            return Response({"message": "Thiếu user_id hoặc mã OTP."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
            profile = user.profile
        except (User.DoesNotExist, AttributeError):
            return Response({"message": "Thông tin người dùng không hợp lệ."}, status=status.HTTP_400_BAD_REQUEST)

        if not profile.two_factor_enabled or not profile.two_factor_secret:
            return Response({"message": "Xác thực 2 lớp chưa được kích hoạt trên tài khoản này."}, status=status.HTTP_400_BAD_REQUEST)

        totp = pyotp.TOTP(profile.two_factor_secret)
        if totp.verify(code):
            # Login successful: Issue tokens
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
        else:
            return Response({"message": "Mã xác minh OTP không đúng hoặc đã hết hạn."}, status=status.HTTP_400_BAD_REQUEST)
