import logging
import sys
from django.conf import settings
from django.core.mail import get_connection, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from gym_booking_backend.infrastructure.models import EmailSetting

logger = logging.getLogger(__name__)


def send_dynamic_recovery_email(user_email: str, reset_link: str, username: str = None) -> bool:
    """
    Khởi tạo kết nối SMTP động từ Cơ sở dữ liệu và gửi email khôi phục mật khẩu.
    
    :param user_email: Địa chỉ nhận thư
    :param reset_link: Đường dẫn khôi phục mật khẩu dạng mã hóa dùng một lần
    :param username: Tên đăng nhập của tài khoản cần khôi phục mật khẩu
    :return: True nếu gửi thành công, False nếu thất bại
    """
    # 1. Đọc tài khoản email SMTP đang được kích hoạt từ database
    smtp_setting = EmailSetting.objects.filter(is_active=True).first()
    
    # Kiểm tra xem hệ thống có đang chạy unit test hay không
    is_testing = 'test' in sys.argv or 'test_coverage' in sys.argv

    try:
        if is_testing or not smtp_setting:
            # Chế độ kiểm thử hoặc chưa cấu hình SMTP -> Fallback về cấu hình mặc định (ví dụ console backend hoặc locmem)
            connection = get_connection()
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@gym.local')
            if not is_testing:
                logger.warning("Hệ thống chưa thiết lập cấu hình SMTP động. Sử dụng cấu hình mặc định.")
        else:
            # 2. Tạo kết nối (Connection) SMTP động từ thông số trong Database
            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=smtp_setting.email_host,
                port=smtp_setting.email_port,
                username=smtp_setting.email_host_user,
                password=smtp_setting.email_host_password,
                use_tls=smtp_setting.email_use_tls,
                fail_silently=False
            )
            from_email = smtp_setting.email_host_user

        # 3. Kết xuất giao diện email bằng HTML Template và truyền tham số
        context = {
            'reset_link': reset_link,
            'email_user': user_email,
            'username': username
        }
        html_content = render_to_string('pt/reset_password_email.html', context)
        
        # Tạo body thuần văn bản (plain text) sạch đẹp và tương thích tốt nhất
        user_info = f" cho tài khoản '{username}'" if username else ""
        text_content = (
            f"Chào bạn,\n\n"
            f"Chúng tôi đã nhận được yêu cầu khôi phục mật khẩu{user_info} được đăng ký với email này ({user_email}).\n\n"
            f"Vui lòng nhấn vào liên kết dưới đây để đặt lại mật khẩu của bạn:\n"
            f"{reset_link}\n\n"
            f"Lưu ý: Liên kết này chỉ có hiệu lực sử dụng một lần và sẽ tự động hết hạn.\n\n"
            f"Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này.\n\n"
            f"Trân trọng,\n"
            f"Gym Booking Support"
        )

        # 4. Thiết lập nội dung thư khôi phục
        subject = f"[Gym Booking] Yêu cầu khôi phục mật khẩu tài khoản {username}" if username else "[Gym Booking] Yêu cầu khôi phục mật khẩu tài khoản"
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[user_email],
            connection=connection  # Chỉ định kết nối động
        )
        email.attach_alternative(html_content, "text/html")

        # 5. Thực hiện gửi thư và đóng kết nối
        email.send(fail_silently=False)
        return True

    except Exception as exc:
        # Ghi nhận log chi tiết nếu kết nối SMTP bị lỗi (như sai tài khoản, chặn cổng,...)
        logger.error(f"Lỗi khi gửi email khôi phục mật khẩu đến {user_email}: {str(exc)}")
        return False
