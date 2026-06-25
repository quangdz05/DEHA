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
    schedule_service,
)
from gym_booking_backend.application.use_cases import (
    cancel_booking,
    create_booking,
    create_membership,
    create_payment,
    create_review,
    register_user,
    update_profile,
)
from gym_booking_backend.domain.exceptions import GymException
from gym_booking_backend.presentation.serializers import (
    BookingSerializer,
    CategorySerializer,
    ClassScheduleSerializer,
    GymClassSerializer,
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


class CategoryListAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        result = catalog_service.get_categories()
        return self.handle_result(result, CategorySerializer, many=True)


class RoomListAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from gym_booking_backend.infrastructure.models import Room
        from gym_booking_backend.presentation.serializers import RoomSerializer
        return Response(RoomSerializer(Room.objects.all(), many=True).data)


class GymClassListAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        result = catalog_service.get_classes(
            category_id=request.query_params.get("category"),
            trainer_id=request.query_params.get("trainer"),
        )
        return self.handle_result(result, GymClassSerializer, many=True)


class GymClassDetailAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request, class_id):
        result = catalog_service.get_class(class_id)
        return self.handle_result(result, GymClassSerializer)


class ScheduleListAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        result = schedule_service.get_schedules(
            date=request.query_params.get("date"),
            trainer_id=request.query_params.get("trainer"),
            available=request.query_params.get("available") == "true",
        )
        return self.handle_result(result, ClassScheduleSerializer, many=True)


class ScheduleDetailAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request, schedule_id):
        result = schedule_service.get_schedule(schedule_id)
        return self.handle_result(result, ClassScheduleSerializer)


class BookingCreateAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = create_booking.execute(
            request.user,
            serializer.validated_data["schedule"].id,
            serializer.validated_data.get("note", ""),
        )
        return self.handle_result(result, BookingSerializer)


class MyBookingsAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result = booking_service.get_my_bookings(request.user)
        return self.handle_result(result, BookingSerializer, many=True)


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


class BookingCancelAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        reason = request.data.get("cancellation_reason", "")
        result = cancel_booking.execute(request.user, booking_id, reason)
        return self.handle_result(result, BookingSerializer)


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


class ClassReviewsAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request, class_id):
        result = review_service.get_reviews_by_class(class_id)
        return self.handle_result(result, ReviewSerializer, many=True)


class AdminBookingListAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        from gym_booking_backend.infrastructure.models import Booking
        bookings = Booking.objects.select_related("user__profile", "schedule__gym_class", "schedule__trainer", "schedule__room").all()
        return self.handle_result(Result.success_result(bookings), BookingSerializer, many=True)


class AdminBookingStatusAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        from gym_booking_backend.infrastructure.models import Booking
        from gym_booking_backend.domain.constants import BookingStatus, ScheduleStatus
        booking = Booking.objects.filter(id=booking_id).first()
        if not booking:
            return self.handle_result(Result.failure_result("Booking not found.", status_code=404))
        
        new_status = request.data.get("status")
        if new_status not in BookingStatus.values:
            return self.handle_result(Result.failure_result("Invalid status.", status_code=400))
        
        old_status = booking.status
        booking.status = new_status
        
        if new_status == BookingStatus.CANCELLED and old_status != BookingStatus.CANCELLED:
            schedule = booking.schedule
            if schedule.current_participants > 0:
                schedule.current_participants -= 1
            if schedule.status == ScheduleStatus.FULL:
                schedule.status = ScheduleStatus.OPEN
            schedule.save(update_fields=["current_participants", "status", "updated_at"])
        elif old_status == BookingStatus.CANCELLED and new_status != BookingStatus.CANCELLED:
            schedule = booking.schedule
            schedule.current_participants += 1
            if schedule.current_participants >= schedule.max_participants:
                schedule.status = ScheduleStatus.FULL
            schedule.save(update_fields=["current_participants", "status", "updated_at"])
            
        booking.save(update_fields=["status"])
        return self.handle_result(Result.success_result(booking), BookingSerializer)


class AdminScheduleBookingListAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, schedule_id):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))

        from gym_booking_backend.infrastructure.models import Booking, ClassSchedule

        schedule = ClassSchedule.objects.filter(id=schedule_id).first()
        if not schedule:
            return self.handle_result(Result.failure_result("Schedule not found.", status_code=404))

        bookings = Booking.objects.select_related("user__profile").filter(schedule_id=schedule_id)
        data = []
        for b in bookings:
            profile = getattr(b.user, "profile", None)
            data.append({
                "id": b.id,
                "booking_code": b.booking_code,
                "username": b.user.username,
                "full_name": profile.full_name if profile else b.user.username,
                "phone": profile.phone if profile else "",
                "status": b.status,
                "booked_at": b.booked_at,
                "health_notes": profile.health_notes if profile else "",
                "fitness_goals": profile.fitness_goals if profile else "",
                "emergency_contact_name": profile.emergency_contact_name if profile else "",
                "emergency_contact_phone": profile.emergency_contact_phone if profile else "",
            })
        return self.handle_result(Result.success_result(data))


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


class TrainerScheduleListAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "trainer":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        from gym_booking_backend.infrastructure.models import Trainer, ClassSchedule
        trainer = Trainer.objects.filter(user=request.user).first()
        if not trainer:
            return self.handle_result(Result.failure_result("Trainer profile not linked to user.", status_code=404))
        schedules = ClassSchedule.objects.select_related("gym_class", "trainer", "room").filter(trainer=trainer)
        return self.handle_result(Result.success_result(schedules), ClassScheduleSerializer, many=True)


class TrainerScheduleBookingListAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, schedule_id):
        if not hasattr(request.user, "profile") or request.user.profile.role != "trainer":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        from gym_booking_backend.infrastructure.models import Trainer, ClassSchedule, Booking
        trainer = Trainer.objects.filter(user=request.user).first()
        if not trainer:
            return self.handle_result(Result.failure_result("Trainer profile not linked to user.", status_code=404))
        
        schedule = ClassSchedule.objects.filter(id=schedule_id, trainer=trainer).first()
        if not schedule:
            return self.handle_result(Result.failure_result("Schedule not found or does not belong to you.", status_code=404))
            
        bookings = Booking.objects.select_related("user__profile").filter(schedule_id=schedule_id)
        data = []
        for b in bookings:
            profile = getattr(b.user, "profile", None)
            data.append({
                "id": b.id,
                "booking_code": b.booking_code,
                "username": b.user.username,
                "full_name": profile.full_name if profile else b.user.username,
                "phone": profile.phone if profile else "",
                "status": b.status,
                "booked_at": b.booked_at,
                "health_notes": profile.health_notes if profile else "",
                "fitness_goals": profile.fitness_goals if profile else "",
                "emergency_contact_name": profile.emergency_contact_name if profile else "",
                "emergency_contact_phone": profile.emergency_contact_phone if profile else "",
            })
        return self.handle_result(Result.success_result(data))


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
        if not hasattr(request.user, "profile") or request.user.profile.role != "trainer":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        
        from gym_booking_backend.infrastructure.models import Trainer, Booking
        trainer = Trainer.objects.filter(user=request.user).first()
        if not trainer:
            return self.handle_result(Result.failure_result("Trainer profile not linked to user.", status_code=404))

        booking = Booking.objects.filter(id=booking_id, schedule__trainer=trainer).first()
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
        if not hasattr(request.user, "profile") or request.user.profile.role != "trainer":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        from gym_booking_backend.infrastructure.models import Trainer, Review
        trainer = Trainer.objects.filter(user=request.user).first()
        if not trainer:
            return self.handle_result(Result.failure_result("Trainer profile not linked to user.", status_code=404))
        reviews = Review.objects.filter(trainer=trainer)
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


class AdminCreateScheduleAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        
        from django.core.exceptions import ValidationError
        from gym_booking_backend.presentation.serializers import ClassScheduleSerializer
        serializer = ClassScheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            schedule = serializer.save()
            return self.handle_result(Result.success_result(schedule, status_code=201), ClassScheduleSerializer)
        except ValidationError as exc:
            msg = exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            return self.handle_result(Result.failure_result(str(msg), status_code=400))
        except Exception as exc:
            return self.handle_result(Result.failure_result(str(exc), status_code=400))


class AdminScheduleDetailAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def _require_admin(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))
        return None

    def patch(self, request, schedule_id):
        deny = self._require_admin(request)
        if deny:
            return deny

        from django.core.exceptions import ValidationError
        from gym_booking_backend.infrastructure.models import ClassSchedule

        schedule = ClassSchedule.objects.filter(id=schedule_id).first()
        if not schedule:
            return self.handle_result(Result.failure_result("Schedule not found.", status_code=404))

        serializer = ClassScheduleSerializer(schedule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            schedule = serializer.save()
            return self.handle_result(Result.success_result(schedule), ClassScheduleSerializer)
        except ValidationError as exc:
            msg = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            return self.handle_result(Result.failure_result(str(msg), status_code=400))
        except Exception as exc:
            return self.handle_result(Result.failure_result(str(exc), status_code=400))

    def delete(self, request, schedule_id):
        deny = self._require_admin(request)
        if deny:
            return deny

        from gym_booking_backend.infrastructure.models import ClassSchedule

        schedule = ClassSchedule.objects.filter(id=schedule_id).first()
        if not schedule:
            return self.handle_result(Result.failure_result("Schedule not found.", status_code=404))

        schedule.delete()
        return self.handle_result(Result.success_result({"message": "Deleted schedule successfully."}))


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


class AdminCreateGymClassAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return self.handle_result(Result.failure_result("Permission denied.", status_code=403))

        from gym_booking_backend.infrastructure.models import GymClass, Category, Trainer as TrainerModel

        name = request.data.get("name", "").strip()
        category_id = request.data.get("category")
        trainer_id = request.data.get("trainer")
        description = request.data.get("description", "")
        difficulty_level = request.data.get("difficulty_level", "beginner")
        duration_minutes = request.data.get("duration_minutes", 60)
        price = request.data.get("price", 0)

        if not name or not category_id or not trainer_id:
            return self.handle_result(Result.failure_result("Tên lớp, danh mục và HLV là bắt buộc.", status_code=400))

        category = Category.objects.filter(id=category_id).first()
        if not category:
            return self.handle_result(Result.failure_result("Danh mục không tồn tại.", status_code=400))

        trainer = TrainerModel.objects.filter(id=trainer_id).first()
        if not trainer:
            return self.handle_result(Result.failure_result("Huấn luyện viên không tồn tại.", status_code=400))

        if GymClass.objects.filter(name=name).exists():
            return self.handle_result(Result.failure_result(f"Lớp tập '{name}' đã tồn tại.", status_code=400))

        try:
            gym_class = GymClass.objects.create(
                name=name,
                category=category,
                trainer=trainer,
                description=description,
                difficulty_level=difficulty_level,
                duration_minutes=int(duration_minutes),
                price=float(price or 0),
            )
            return self.handle_result(Result.success_result(gym_class, status_code=201), GymClassSerializer)
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
