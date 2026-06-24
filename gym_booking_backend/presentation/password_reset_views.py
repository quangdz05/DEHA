from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from urllib.parse import urlparse

class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip()
        if not email:
            return Response({"message": "Vui lòng nhập địa chỉ email."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        # To avoid email enumeration, we return success even if the email does not exist
        msg = "Nếu email tồn tại trong hệ thống, bạn sẽ nhận được đường dẫn khôi phục mật khẩu."

        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Dynamically determine the frontend domain/port from Referer
            referer = request.META.get("HTTP_REFERER")
            if referer:
                parsed = urlparse(referer)
                frontend_base = f"{parsed.scheme}://{parsed.netloc}"
            else:
                frontend_base = "http://localhost:5500"

            reset_link = f"{frontend_base}/reset-password.html?uid={uid}&token={token}"

            try:
                send_mail(
                    subject="Khôi phục mật khẩu - Gym Booking",
                    message=f"Chào {user.get_full_name() or user.username},\n\nVui lòng nhấn vào liên kết dưới đây để đặt lại mật khẩu của bạn:\n{reset_link}\n\nLiên kết này có hiệu lực một lần và sẽ hết hạn sau khi sử dụng.\n\nTrân trọng,\nGym Booking Support",
                    from_email="noreply@gym.local",
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                # Log the error but don't crash
                print("Failed to send email:", e)
                return Response({"message": "Lỗi hệ thống khi gửi email khôi phục."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": msg}, status=status.HTTP_200_OK)

class ResetPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get("uid", "")
        token = request.data.get("token", "")
        new_password = request.data.get("new_password", "")

        if not uid or not token or not new_password:
            return Response({"message": "Thiếu thông tin yêu cầu đặt lại mật khẩu."}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({"message": "Mật khẩu mới phải có ít nhất 8 ký tự."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid_dec = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_dec)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"message": "Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"message": "Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"message": "Đặt lại mật khẩu thành công!"}, status=status.HTTP_200_OK)
