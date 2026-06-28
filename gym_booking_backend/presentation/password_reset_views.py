from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from urllib.parse import urlparse

from gym_booking_backend.domain.result import Result
from gym_booking_backend.presentation.views import BaseAPIView


class ForgotPasswordAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip()
        if not email:
            return self.handle_result(Result.failure_result("Vui lòng nhập địa chỉ email.", status_code=400))

        users = User.objects.filter(email=email)
        if not users.exists():
            return self.handle_result(Result.failure_result("Địa chỉ email không tồn tại trong hệ thống.", status_code=400))

        # Dynamically determine the frontend domain/port from Referer
        referer = request.META.get("HTTP_REFERER")
        if referer:
            parsed = urlparse(referer)
            frontend_base = f"{parsed.scheme}://{parsed.netloc}"
        else:
            frontend_base = "http://localhost:5500"

        from gym_booking_backend.application.services.email_service import send_dynamic_recovery_email
        
        any_success = False
        last_error = None

        for user in users:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = f"{frontend_base}/reset-password.html?uid={uid}&token={token}"
            
            try:
                success = send_dynamic_recovery_email(email, reset_link, username=user.username)
                if success:
                    any_success = True
                else:
                    last_error = "Lỗi hệ thống khi gửi email khôi phục."
            except ValueError as val_err:
                last_error = str(val_err)
            except Exception as e:
                print(f"Failed to send email for user {user.username}:", e)
                last_error = "Lỗi hệ thống khi gửi email khôi phục."

        if not any_success:
            return self.handle_result(Result.failure_result(last_error or "Lỗi hệ thống khi gửi email khôi phục.", status_code=500))

        return self.handle_result(Result.success_result({"message": "Liên kết khôi phục mật khẩu đã được gửi đến email của bạn."}, status_code=200))


class ResetPasswordAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get("uid", "")
        token = request.data.get("token", "")
        new_password = request.data.get("new_password", "")

        if not uid or not token or not new_password:
            return self.handle_result(Result.failure_result("Thiếu thông tin yêu cầu đặt lại mật khẩu.", status_code=400))

        if len(new_password) < 8:
            return self.handle_result(Result.failure_result("Mật khẩu mới phải có ít nhất 8 ký tự.", status_code=400))

        try:
            uid_dec = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_dec)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return self.handle_result(Result.failure_result("Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.", status_code=400))

        if not default_token_generator.check_token(user, token):
            return self.handle_result(Result.failure_result("Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.", status_code=400))

        user.set_password(new_password)
        user.save()

        return self.handle_result(Result.success_result({"message": "Đặt lại mật khẩu thành công!"}, status_code=200))
