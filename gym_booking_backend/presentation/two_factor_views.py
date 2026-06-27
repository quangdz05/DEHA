import pyotp
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

from gym_booking_backend.domain.result import Result
from gym_booking_backend.presentation.views import BaseAPIView
from gym_booking_backend.presentation.jwt_views import set_refresh_cookie


class TwoFactorSetupAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = getattr(request.user, "profile", None)
        if not profile:
            from gym_booking_backend.infrastructure.models import Profile
            profile = Profile.objects.create(user=request.user, full_name=request.user.username)

        if profile.two_factor_enabled:
            return self.handle_result(Result.failure_result("Tài khoản của bạn đã được bật 2FA trước đó.", status_code=400))

        email = (request.user.email or "").strip()
        if not email:
            return self.handle_result(Result.failure_result("Tài khoản chưa có email. Vui lòng cập nhật email trước khi kích hoạt xác thực 2 lớp.", status_code=400))

        if User.objects.filter(email=email).exclude(id=request.user.id).exists():
            return self.handle_result(Result.failure_result("Email này đã được sử dụng bởi một tài khoản khác. Mỗi tài khoản chỉ được dùng 1 email duy nhất.", status_code=400))

        # Generate new base32 secret
        secret = pyotp.random_base32()
        profile.two_factor_secret = secret
        profile.save(update_fields=["two_factor_secret"])

        # Create provisioning URI for Authenticator apps
        totp = pyotp.TOTP(secret)
        email = request.user.email or request.user.username
        provisioning_uri = totp.provisioning_uri(name=email, issuer_name="GymBooking")

        return self.handle_result(Result.success_result({
            "secret": secret,
            "provisioning_uri": provisioning_uri
        }, status_code=200))


class TwoFactorEnableAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get("code", "").strip()
        profile = getattr(request.user, "profile", None)

        if not profile or not profile.two_factor_secret:
            return self.handle_result(Result.failure_result("Vui lòng gọi API Setup trước để khởi tạo 2FA.", status_code=400))

        if profile.two_factor_enabled:
            return self.handle_result(Result.failure_result("Tài khoản của bạn đã bật 2FA rồi.", status_code=400))

        totp = pyotp.TOTP(profile.two_factor_secret)
        if totp.verify(code):
            profile.two_factor_enabled = True
            profile.save(update_fields=["two_factor_enabled"])
            return self.handle_result(Result.success_result({"message": "Kích hoạt xác thực 2 lớp (2FA) thành công!"}, status_code=200))
        else:
            return self.handle_result(Result.failure_result("Mã xác minh OTP không đúng hoặc đã hết hạn.", status_code=400))


class TwoFactorDisableAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get("code", "").strip()
        profile = getattr(request.user, "profile", None)

        if not profile or not profile.two_factor_enabled:
            return self.handle_result(Result.failure_result("Tài khoản của bạn chưa kích hoạt 2FA.", status_code=400))

        # Require verification to disable
        totp = pyotp.TOTP(profile.two_factor_secret)
        if totp.verify(code):
            profile.two_factor_enabled = False
            profile.two_factor_secret = ""
            profile.save(update_fields=["two_factor_enabled", "two_factor_secret"])
            return self.handle_result(Result.success_result({"message": "Đã hủy kích hoạt xác thực 2 lớp (2FA)."}, status_code=200))
        else:
            return self.handle_result(Result.failure_result("Mã xác minh OTP không đúng hoặc đã hết hạn.", status_code=400))


class TwoFactorVerifyAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get("user_id")
        code = request.data.get("code", "").strip()

        if not user_id or not code:
            return self.handle_result(Result.failure_result("Thiếu user_id hoặc mã OTP.", status_code=400))

        try:
            user = User.objects.get(id=user_id)
            profile = user.profile
        except (User.DoesNotExist, AttributeError):
            return self.handle_result(Result.failure_result("Thông tin người dùng không hợp lệ.", status_code=400))

        if not profile.two_factor_enabled or not profile.two_factor_secret:
            return self.handle_result(Result.failure_result("Xác thực 2 lớp chưa được kích hoạt trên tài khoản này.", status_code=400))

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

            data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": profile.role,
                "full_name": profile.full_name,
                "two_factor_enabled": profile.two_factor_enabled,
                "access": access_token
            }
            
            response = self.handle_result(Result.success_result(data, status_code=200))
            set_refresh_cookie(response, refresh_token)
            return response
        else:
            return self.handle_result(Result.failure_result("Mã xác minh OTP không đúng hoặc đã hết hạn.", status_code=400))
