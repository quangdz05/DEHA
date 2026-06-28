from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from gym_booking_backend.domain.result import Result

class BaseAPIView(APIView):
    def handle_result(self, result: Result, serializer_class=None, many=False, context=None) -> Response:
        if not result.success:
            return Response({"message": result.message}, status=result.status_code)
        
        if serializer_class and result.data is not None:
            ctx = context or {"request": self.request}
            serialized_data = serializer_class(result.data, many=many, context=ctx).data
            return Response(serialized_data, status=result.status_code)
        
        if isinstance(result.data, dict) or isinstance(result.data, list):
            return Response(result.data, status=result.status_code)
            
        return Response({"message": result.message}, status=result.status_code)


from gym_booking_backend.application.services import (
    auth_service,
    booking_service,
    catalog_service,
    membership_service,
    payment_service,
    profile_service,
    review_service,
)
from gym_booking_backend.application.use_cases import (
    create_membership,
    create_payment,
    create_review,
    register_user,
    update_profile,
)
from gym_booking_backend.domain.exceptions import GymException
from gym_booking_backend.presentation.serializers import (
    MembershipPackageSerializer,
    PaymentSerializer,
    ProfileSerializer,
    ReviewSerializer,
    TrainerSerializer,
    TrainerBookingSerializer,
    TrainerMonthlyBookingSerializer,
    UserMembershipSerializer,
    UserRegisterSerializer,
)


def error_response(exc, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({"message": str(exc)}, status=status_code)


class RegisterAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = register_user.execute(
            username=data["username"],
            email=data.get("email", ""),
            password=data["password"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            role=data.get("role", "member"),
        )
        if not result.success:
            return self.handle_result(result)
        
        user = result.data
        role = "member"
        if hasattr(user, "profile"):
            role = user.profile.role

        return Response(
            {"id": user.id, "username": user.username, "email": user.email, "role": role},
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        result = auth_service.login_user(
            request,
            request.data.get("username", ""),
            request.data.get("password", ""),
        )
        if not result.success:
            return self.handle_result(result)

        user = result.data
        from gym_booking_backend.domain.constants import UserRole
        from gym_booking_backend.infrastructure.models import Profile
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={"full_name": user.get_full_name() or user.username}
        )

        if (user.is_superuser or user.is_staff) and profile.role != UserRole.ADMIN:
            profile.role = UserRole.ADMIN
            profile.save()

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": profile.role,
            "full_name": profile.full_name
        })


class LogoutAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        result = auth_service.logout_user(request)
        return self.handle_result(result)


class ProfileMeAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_authenticated:
            from django.contrib.auth import login as django_login
            if not getattr(request.user, "backend", None):
                request.user.backend = 'django.contrib.auth.backends.ModelBackend'
            if int(request.session.get('_auth_user_id', 0)) != request.user.id:
                django_login(request, request.user)

        result = profile_service.get_my_profile(request.user)
        return self.handle_result(result, ProfileSerializer)

    def put(self, request):
        serializer = ProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        result = update_profile.execute(request.user, serializer.validated_data)
        return self.handle_result(result, ProfileSerializer)


class TrainerListAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        result = catalog_service.get_trainers()
        return self.handle_result(result, TrainerSerializer, many=True)


class TrainerDetailAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request, trainer_id):
        result = catalog_service.get_trainer(trainer_id)
        return self.handle_result(result, TrainerSerializer)


class RoomListAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from gym_booking_backend.infrastructure.models import Room
        from gym_booking_backend.presentation.serializers import RoomSerializer
        return Response(RoomSerializer(Room.objects.all(), many=True).data)


class TrainerScheduleDetailAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from gym_booking_backend.infrastructure.models import Trainer, TrainerSchedule
        from datetime import timedelta
        from django.utils import timezone
        from gym_booking_backend.application.services.pt_booking_service import get_trainer_busy_slots
        from gym_booking_backend.domain.constants import WeekdayChoices

        # Enforce trainer restriction: trainers can only view their own schedule
        if hasattr(request.user, "profile") and request.user.profile.role == "trainer":
            logged_in_trainer = Trainer.objects.filter(user=request.user).first()
            if not logged_in_trainer:
                return self.handle_result(Result.failure_result("Không tìm thấy hồ sơ huấn luyện viên liên kết.", status_code=404))
            
            trainer_id = request.query_params.get("trainer_id")
            if trainer_id:
                try:
                    tid_int = int(trainer_id)
                except ValueError:
                    return self.handle_result(Result.failure_result("Mã huấn luyện viên không hợp lệ.", status_code=400))
                if tid_int != logged_in_trainer.id:
                    return self.handle_result(Result.failure_result("Huấn luyện viên chỉ có quyền xem lịch của chính mình.", status_code=403))
            
            trainer = logged_in_trainer
        else:
            trainer_id = request.query_params.get("trainer_id")
            if trainer_id:
                try:
                    trainer = Trainer.objects.filter(id=int(trainer_id)).first()
                except ValueError:
                    return self.handle_result(Result.failure_result("Mã huấn luyện viên không hợp lệ.", status_code=400))
                if not trainer:
                    return self.handle_result(Result.failure_result("Không tìm thấy huấn luyện viên.", status_code=404))
            else:
                # Default to the logged-in trainer
                trainer = Trainer.objects.filter(user=request.user).first()
                if not trainer:
                    return self.handle_result(Result.failure_result("Vui lòng chọn huấn luyện viên.", status_code=400))

        # Get weekly availability
        schedules = TrainerSchedule.objects.filter(trainer=trainer, is_available=True)
        schedule_data = [
            {
                "weekday": s.weekday,
                "weekday_name": dict(WeekdayChoices.choices).get(s.weekday, str(s.weekday)),
                "start_time": s.start_time.strftime("%H:%M") if s.start_time else "",
                "end_time": s.end_time.strftime("%H:%M") if s.end_time else ""
            }
            for s in schedules
        ]

        # Get busy slots for the next 14 days
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=14)
        busy_slots = get_trainer_busy_slots(trainer, start_date, end_date)

        return self.handle_result(Result.success_result({
            "trainer": {
                "id": trainer.id,
                "name": trainer.name,
                "specialty": trainer.specialty
            },
            "weekly_availability": schedule_data,
            "busy_slots": busy_slots
        }))

    def put(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "trainer":
            return self.handle_result(Result.failure_result("Chỉ huấn luyện viên mới có quyền cập nhật lịch làm việc.", status_code=403))

        from gym_booking_backend.infrastructure.models import Trainer, TrainerSchedule
        from datetime import datetime, time

        trainer = Trainer.objects.filter(user=request.user).first()
        if not trainer:
            return self.handle_result(Result.failure_result("Không tìm thấy hồ sơ huấn luyện viên liên kết.", status_code=404))

        schedules_data = request.data
        if not isinstance(schedules_data, list):
            return self.handle_result(Result.failure_result("Dữ liệu gửi lên phải là một danh sách các ngày.", status_code=400))

        validated_items = []
        for idx, item in enumerate(schedules_data):
            weekday = item.get("weekday")
            if weekday is None or not (0 <= int(weekday) <= 6):
                return self.handle_result(Result.failure_result(f"Thứ tự ngày không hợp lệ ở vị trí {idx}.", status_code=400))
            
            is_available = item.get("is_available", False)
            start_time_str = item.get("start_time")
            end_time_str = item.get("end_time")

            start_time = time(9, 0)
            end_time = time(17, 0)

            if is_available:
                if not start_time_str or not end_time_str:
                    return self.handle_result(Result.failure_result(f"Vui lòng cung cấp giờ bắt đầu và kết thúc cho ngày khả dụng ở vị trí {idx}.", status_code=400))
                try:
                    start_time = datetime.strptime(start_time_str, "%H:%M").time()
                    end_time = datetime.strptime(end_time_str, "%H:%M").time()
                except ValueError:
                    try:
                        start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
                        end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()
                    except ValueError:
                        return self.handle_result(Result.failure_result(f"Giờ không đúng định dạng HH:MM ở vị trí {idx}.", status_code=400))

                if start_time >= end_time:
                    return self.handle_result(Result.failure_result(f"Giờ bắt đầu phải trước giờ kết thúc ở vị trí {idx}.", status_code=400))

            validated_items.append({
                "weekday": int(weekday),
                "is_available": bool(is_available),
                "start_time": start_time,
                "end_time": end_time
            })

        for item in validated_items:
            TrainerSchedule.objects.update_or_create(
                trainer=trainer,
                weekday=item["weekday"],
                defaults={
                    "is_available": item["is_available"],
                    "start_time": item["start_time"],
                    "end_time": item["end_time"]
                }
            )

        return self.handle_result(Result.success_result({"message": "Cập nhật lịch làm việc hàng tuần thành công!"}))





class TrainerBookingCreateAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TrainerBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = booking_service.create_trainer_booking(
            request.user,
            data["trainer"].id,
            data["start_time"],
            data["end_time"],
            data.get("note", ""),
        )
        return self.handle_result(result, TrainerBookingSerializer)


class MyTrainerBookingsAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result = booking_service.get_my_trainer_bookings(request.user)
        return self.handle_result(result, TrainerBookingSerializer, many=True)


class TrainerBookingCancelAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        reason = request.data.get("cancellation_reason", "")
        result = booking_service.cancel_trainer_booking(request.user, booking_id, reason)
        return self.handle_result(result, TrainerBookingSerializer)


class TrainerMonthlyBookingCreateAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TrainerMonthlyBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = booking_service.create_trainer_monthly_booking(
            request.user,
            data["trainer"].id,
            data["start_date"],
            data.get("months", 1),
            data.get("sessions_per_week", 3),
            data.get("preferred_time"),
            data.get("note", ""),
        )
        return self.handle_result(result, TrainerMonthlyBookingSerializer)


class MyTrainerMonthlyBookingsAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result = booking_service.get_my_trainer_monthly_bookings(request.user)
        return self.handle_result(result, TrainerMonthlyBookingSerializer, many=True)


class TrainerMonthlyBookingCancelAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        reason = request.data.get("cancellation_reason", "")
        result = booking_service.cancel_trainer_monthly_booking(request.user, booking_id, reason)
        return self.handle_result(result, TrainerMonthlyBookingSerializer)





class MembershipPackageListAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        result = membership_service.get_active_packages()
        return self.handle_result(result, MembershipPackageSerializer, many=True)


class MembershipCreateAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        result = create_membership.execute(request.user, request.data.get("package"))
        return self.handle_result(result, UserMembershipSerializer)


class MyMembershipsAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result = membership_service.get_my_memberships(request.user)
        return self.handle_result(result, UserMembershipSerializer, many=True)


class MembershipCancelAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, membership_id):
        result = membership_service.cancel_membership(request.user, membership_id)
        return self.handle_result(result, UserMembershipSerializer)


class PaymentCreateAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = create_payment.execute(
            request.user,
            serializer.validated_data["membership"].id,
            serializer.validated_data["payment_method"],
        )
        return self.handle_result(result, PaymentSerializer)


class MyPaymentsAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result = payment_service.get_my_payments(request.user)
        return self.handle_result(result, PaymentSerializer, many=True)


class PaymentConfirmAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_id):
        from gym_booking_backend.infrastructure.models import Payment

        payment_obj = Payment.objects.filter(id=payment_id).first()
        if not payment_obj:
            return Response({"message": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        is_admin = hasattr(request.user, "profile") and request.user.profile.role == "admin"
        if payment_obj.user_id != request.user.id and not is_admin:
            return Response({"message": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        result = payment_service.confirm_payment(payment_id)
        return self.handle_result(result, PaymentSerializer)


class TrainerBookingPaymentCreateAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        payment_method = request.data.get("payment_method", "")
        if not payment_method:
            return Response({"message": "payment_method is required."}, status=status.HTTP_400_BAD_REQUEST)

        result = payment_service.create_trainer_booking_payment(
            user=request.user,
            trainer_booking_id=booking_id,
            payment_method=payment_method,
        )
        return self.handle_result(result, PaymentSerializer)


class ReviewCreateAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = create_review.execute(
            user=request.user,
            trainer_id=data["trainer"].id if data.get("trainer") else None,
            gym_class_id=data["gym_class"].id if data.get("gym_class") else None,
            rating=data.get("rating"),
            comment=data.get("comment", ""),
        )
        return self.handle_result(result, ReviewSerializer)


class TrainerReviewsAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request, trainer_id):
        result = review_service.get_reviews_by_trainer(trainer_id)
        return self.handle_result(result, ReviewSerializer, many=True)





class AdminTrainerMonthlyBookingListAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result = booking_service.get_all_trainer_monthly_bookings(request.user)
        return self.handle_result(result, TrainerMonthlyBookingSerializer, many=True)


class AdminTrainerMonthlyBookingStatusAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        result = booking_service.update_admin_trainer_monthly_booking_status(booking_id, request.data.get("status"))
        return self.handle_result(result, TrainerMonthlyBookingSerializer)


class AdminPaymentListAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        from gym_booking_backend.infrastructure.models import Payment
        payments = Payment.objects.select_related("user__profile", "membership__package").all()
        return self.handle_result(Result.success_result(payments), PaymentSerializer, many=True)


class AdminPaymentConfirmAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_id):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        result = payment_service.confirm_payment(payment_id)
        return self.handle_result(result, PaymentSerializer)





class TrainerPersonalBookingListAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result = booking_service.get_trainer_personal_bookings(request.user)
        return self.handle_result(result, TrainerBookingSerializer, many=True)


class TrainerPersonalBookingStatusAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        new_status = request.data.get("status")
        result = booking_service.update_trainer_booking_status(request.user, booking_id, new_status)
        return self.handle_result(result, TrainerBookingSerializer)


class TrainerMonthlyBookingListAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result = booking_service.get_trainer_monthly_bookings(request.user)
        return self.handle_result(result, TrainerMonthlyBookingSerializer, many=True)


class TrainerMonthlyBookingStatusAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        result = booking_service.update_trainer_monthly_booking_status(request.user, booking_id, request.data.get("status"))
        return self.handle_result(result, TrainerMonthlyBookingSerializer)


class TrainerBookingAttendanceAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        if not hasattr(request.user, "profile") or request.user.profile.role not in ["trainer", "admin"]:
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        
        from gym_booking_backend.infrastructure.models import Trainer, Booking
        is_admin = request.user.profile.role == "admin"
        if not is_admin:
            trainer = Trainer.objects.filter(user=request.user).first()
            if not trainer:
                return self.handle_result(Result.failure_result("Trainer profile not linked to user.", status_code=404))
            booking = Booking.objects.filter(id=booking_id, schedule__trainer=trainer).first()
        else:
            booking = Booking.objects.filter(id=booking_id).first()
            
        if not booking:
            return self.handle_result(Result.failure_result("Booking not found or does not belong to your schedule.", status_code=404))

        new_status = request.data.get("status")
        if new_status not in ["completed", "no_show"]:
            return self.handle_result(Result.failure_result("Invalid status for attendance.", status_code=400))

        booking.status = new_status
        booking.save(update_fields=["status"])

        return self.handle_result(Result.success_result(booking), BookingSerializer)


class MembershipFreezeAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, membership_id):
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        reason = request.data.get("reason", "")

        if not start_date or not end_date:
            return self.handle_result(Result.failure_result("start_date and end_date are required.", status_code=400))

        result = membership_service.freeze_membership(
            user=request.user,
            membership_id=membership_id,
            start_date=start_date,
            end_date=end_date,
            reason=reason
        )
        from gym_booking_backend.presentation.serializers import MembershipFreezeSerializer
        return self.handle_result(result, MembershipFreezeSerializer)


class MyInvoicesAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from gym_booking_backend.infrastructure.models import Invoice
        invoices = Invoice.objects.filter(user=request.user)
        from gym_booking_backend.presentation.serializers import InvoiceSerializer
        return self.handle_result(Result.success_result(invoices), InvoiceSerializer, many=True)


class InvoiceDetailAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, invoice_id):
        from gym_booking_backend.infrastructure.models import Invoice
        invoice = Invoice.objects.filter(id=invoice_id, user=request.user).first()
        if not invoice:
            return self.handle_result(Result.failure_result("Invoice not found.", status_code=404))
        from gym_booking_backend.presentation.serializers import InvoiceSerializer
        return self.handle_result(Result.success_result(invoice), InvoiceSerializer)


class TrainerReviewsListAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role not in ["trainer", "admin"]:
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        from gym_booking_backend.infrastructure.models import Trainer, Review
        is_admin = request.user.profile.role == "admin"
        if not is_admin:
            trainer = Trainer.objects.filter(user=request.user).first()
            if not trainer:
                return self.handle_result(Result.failure_result("Trainer profile not linked to user.", status_code=404))
            reviews = Review.objects.filter(trainer=trainer)
        else:
            reviews = Review.objects.all()
        from gym_booking_backend.presentation.serializers import ReviewSerializer
        return self.handle_result(Result.success_result(reviews), ReviewSerializer, many=True)


class AdminInvoiceListAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        from gym_booking_backend.infrastructure.models import Invoice
        invoices = Invoice.objects.select_related("user__profile").all()
        from gym_booking_backend.presentation.serializers import InvoiceSerializer
        return self.handle_result(Result.success_result(invoices), InvoiceSerializer, many=True)





class AdminCreateUserAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))

        username = request.data.get("username", "").strip()
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")
        full_name = request.data.get("full_name", "").strip()
        phone = request.data.get("phone", "").strip()
        role = request.data.get("role", "member")

        if not username or not password:
            return self.handle_result(Result.failure_result("Tên đăng nhập và mật khẩu là bắt buộc.", status_code=400))

        if role not in ("member", "trainer"):
            return self.handle_result(Result.failure_result("Vai trò phải là 'member' hoặc 'trainer'.", status_code=400))

        from django.contrib.auth.models import User
        if User.objects.filter(username=username).exists():
            return self.handle_result(Result.failure_result(f"Tên đăng nhập '{username}' đã tồn tại.", status_code=400))

        result = register_user.execute(
            username=username,
            email=email,
            password=password,
            first_name=full_name.split(" ", 1)[0] if full_name else "",
            last_name=full_name.split(" ", 1)[1] if " " in full_name else "",
            role=role,
        )
        if not result.success:
            return self.handle_result(result)

        user = result.data
        try:
            # Update profile with additional info
            from gym_booking_backend.infrastructure.models import Profile
            profile, _ = Profile.objects.get_or_create(
                user=user,
                defaults={"full_name": full_name or username}
            )
            profile.full_name = full_name or username
            profile.phone = phone
            profile.role = role
            profile.save()

            # If trainer, create Trainer record
            if role == "trainer":
                from gym_booking_backend.infrastructure.models import Trainer
                specialty = request.data.get("specialty", "General")
                experience_years = int(request.data.get("experience_years", 0))
                Trainer.objects.get_or_create(
                    user=user,
                    defaults={
                        "name": full_name or username,
                        "email": email or f"{username}@gym.local",
                        "phone": phone,
                        "specialty": specialty,
                        "experience_years": experience_years,
                        "session_price": float(request.data.get("session_price", 0)),
                    }
                )

            return self.handle_result(Result.success_result({
                "message": f"Tạo tài khoản '{username}' thành công với vai trò {'Hội viên' if role == 'member' else 'Huấn luyện viên'}.",
                "id": user.id,
                "username": user.username,
                "role": role,
            }, status_code=201))
        except Exception as exc:
            return self.handle_result(Result.failure_result(str(exc), status_code=400))





class AdminCreatePackageAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))

        from gym_booking_backend.infrastructure.models import MembershipPackage

        name = request.data.get("name", "").strip()
        description = request.data.get("description", "")
        price = request.data.get("price")
        duration_days = request.data.get("duration_days")

        if not name or not price or not duration_days:
            return self.handle_result(Result.failure_result("Tên gói, giá và số ngày là bắt buộc.", status_code=400))

        if MembershipPackage.objects.filter(name=name).exists():
            return self.handle_result(Result.failure_result(f"Gói tập '{name}' đã tồn tại.", status_code=400))

        try:
            max_bookings = request.data.get("max_bookings_per_week")
            package = MembershipPackage.objects.create(
                name=name,
                description=description,
                price=float(price),
                duration_days=int(duration_days),
                max_bookings_per_week=int(max_bookings) if max_bookings else None,
                is_freezable=request.data.get("is_freezable", True),
                max_freeze_days=int(request.data.get("max_freeze_days", 30)),
            )
            return self.handle_result(Result.success_result(package, status_code=201), MembershipPackageSerializer)
        except Exception as exc:
            return self.handle_result(Result.failure_result(str(exc), status_code=400))


class AdminPackageDetailAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _require_admin(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        return None

    def patch(self, request, package_id):
        deny = self._require_admin(request)
        if deny:
            return deny

        from gym_booking_backend.infrastructure.models import MembershipPackage

        package = MembershipPackage.objects.filter(id=package_id).first()
        if not package:
            return self.handle_result(Result.failure_result("Package not found.", status_code=404))

        serializer = MembershipPackageSerializer(package, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        package = serializer.save()
        return self.handle_result(Result.success_result(package), MembershipPackageSerializer)

    def delete(self, request, package_id):
        deny = self._require_admin(request)
        if deny:
            return deny

        from gym_booking_backend.infrastructure.models import MembershipPackage

        package = MembershipPackage.objects.filter(id=package_id).first()
        if not package:
            return self.handle_result(Result.failure_result("Package not found.", status_code=404))

        package.delete()
        return self.handle_result(Result.success_result({"message": "Deleted package successfully."}))


class AdminTrainerListCreateAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _require_admin(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        return None

    def get(self, request):
        deny = self._require_admin(request)
        if deny:
            return deny
        from gym_booking_backend.infrastructure.models import Trainer
        trainers = Trainer.objects.all()
        return self.handle_result(Result.success_result(trainers), TrainerSerializer, many=True)

    def post(self, request):
        deny = self._require_admin(request)
        if deny:
            return deny
        serializer = TrainerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trainer = serializer.save()
        return self.handle_result(Result.success_result(trainer, status_code=201), TrainerSerializer)


class AdminTrainerDetailAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _require_admin(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        return None

    def patch(self, request, trainer_id):
        deny = self._require_admin(request)
        if deny:
            return deny

        from gym_booking_backend.infrastructure.models import Trainer

        trainer = Trainer.objects.filter(id=trainer_id).first()
        if not trainer:
            return self.handle_result(Result.failure_result("Trainer not found.", status_code=404))

        serializer = TrainerSerializer(trainer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        trainer = serializer.save()
        return self.handle_result(Result.success_result(trainer), TrainerSerializer)

    def delete(self, request, trainer_id):
        deny = self._require_admin(request)
        if deny:
            return deny

        from django.db.models import ProtectedError
        from gym_booking_backend.infrastructure.models import Trainer

        trainer = Trainer.objects.filter(id=trainer_id).first()
        if not trainer:
            return self.handle_result(Result.failure_result("Trainer not found.", status_code=404))

        try:
            trainer.delete()
        except ProtectedError:
            return self.handle_result(Result.failure_result("Cannot delete trainer because it is still linked to class or schedule.", status_code=400))

        return self.handle_result(Result.success_result({"message": "Deleted trainer successfully."}))
