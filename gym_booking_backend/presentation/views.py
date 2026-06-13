from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            user = register_user.execute(
                username=data["username"],
                email=data.get("email", ""),
                password=data["password"],
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                role=data.get("role", "member"),
            )
        except GymException as exc:
            return error_response(exc)
        
        role = "member"
        if hasattr(user, "profile"):
            role = user.profile.role

        return Response(
            {"id": user.id, "username": user.username, "email": user.email, "role": role},
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            user = auth_service.login_user(
                request,
                request.data.get("username", ""),
                request.data.get("password", ""),
            )
        except GymException as exc:
            return error_response(exc)

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


class LogoutAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        auth_service.logout_user(request)
        return Response({"message": "Logged out successfully."})


class ProfileMeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = profile_service.get_my_profile(request.user)
        return Response(ProfileSerializer(profile, context={"request": request}).data)

    def put(self, request):
        serializer = ProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = update_profile.execute(request.user, serializer.validated_data)
        return Response(ProfileSerializer(profile, context={"request": request}).data)


class TrainerListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(TrainerSerializer(catalog_service.get_trainers(), many=True, context={"request": request}).data)


class TrainerDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, trainer_id):
        trainer = catalog_service.get_trainer(trainer_id)
        if not trainer:
            return error_response("Trainer not found.", status.HTTP_404_NOT_FOUND)
        return Response(TrainerSerializer(trainer, context={"request": request}).data)


class CategoryListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(CategorySerializer(catalog_service.get_categories(), many=True, context={"request": request}).data)


class RoomListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from gym_booking_backend.infrastructure.models import Room
        from gym_booking_backend.presentation.serializers import RoomSerializer
        return Response(RoomSerializer(Room.objects.all(), many=True).data)


class GymClassListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        classes = catalog_service.get_classes(
            category_id=request.query_params.get("category"),
            trainer_id=request.query_params.get("trainer"),
        )
        return Response(GymClassSerializer(classes, many=True, context={"request": request}).data)


class GymClassDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, class_id):
        gym_class = catalog_service.get_class(class_id)
        if not gym_class:
            return error_response("Class not found.", status.HTTP_404_NOT_FOUND)
        return Response(GymClassSerializer(gym_class, context={"request": request}).data)


class ScheduleListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            schedules = schedule_service.get_schedules(
                date=request.query_params.get("date"),
                trainer_id=request.query_params.get("trainer"),
                available=request.query_params.get("available") == "true",
            )
        except GymException as exc:
            return error_response(exc)
        return Response(ClassScheduleSerializer(schedules, many=True, context={"request": request}).data)


class ScheduleDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, schedule_id):
        schedule = schedule_service.get_schedule(schedule_id)
        if not schedule:
            return error_response("Schedule not found.", status.HTTP_404_NOT_FOUND)
        return Response(ClassScheduleSerializer(schedule, context={"request": request}).data)


class BookingCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            booking = create_booking.execute(
                request.user,
                serializer.validated_data["schedule"].id,
                serializer.validated_data.get("note", ""),
            )
        except GymException as exc:
            return error_response(exc)
        return Response(BookingSerializer(booking, context={"request": request}).data, status=status.HTTP_201_CREATED)


class MyBookingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = booking_service.get_my_bookings(request.user)
        return Response(BookingSerializer(bookings, many=True, context={"request": request}).data)


class TrainerBookingCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TrainerBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            booking = booking_service.create_trainer_booking(
                request.user,
                data["trainer"].id,
                data["start_time"],
                data["end_time"],
                data.get("note", ""),
            )
        except GymException as exc:
            return error_response(exc)
        return Response(TrainerBookingSerializer(booking, context={"request": request}).data, status=status.HTTP_201_CREATED)


class MyTrainerBookingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = booking_service.get_my_trainer_bookings(request.user)
        return Response(TrainerBookingSerializer(bookings, many=True, context={"request": request}).data)


class TrainerBookingCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        reason = request.data.get("cancellation_reason", "")
        try:
            booking = booking_service.cancel_trainer_booking(request.user, booking_id, reason)
        except GymException as exc:
            return error_response(exc)
        return Response(TrainerBookingSerializer(booking, context={"request": request}).data)


class TrainerMonthlyBookingCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TrainerMonthlyBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            booking = booking_service.create_trainer_monthly_booking(
                request.user,
                data["trainer"].id,
                data["start_date"],
                data.get("months", 1),
                data.get("sessions_per_week", 3),
                data.get("preferred_time"),
                data.get("note", ""),
            )
        except GymException as exc:
            return error_response(exc)
        return Response(TrainerMonthlyBookingSerializer(booking, context={"request": request}).data, status=status.HTTP_201_CREATED)


class MyTrainerMonthlyBookingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = booking_service.get_my_trainer_monthly_bookings(request.user)
        return Response(TrainerMonthlyBookingSerializer(bookings, many=True, context={"request": request}).data)


class TrainerMonthlyBookingCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        reason = request.data.get("cancellation_reason", "")
        try:
            booking = booking_service.cancel_trainer_monthly_booking(request.user, booking_id, reason)
        except GymException as exc:
            return error_response(exc)
        return Response(TrainerMonthlyBookingSerializer(booking, context={"request": request}).data)


class BookingCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        reason = request.data.get("cancellation_reason", "")
        try:
            booking = cancel_booking.execute(request.user, booking_id, reason)
        except GymException as exc:
            return error_response(exc)
        return Response(BookingSerializer(booking, context={"request": request}).data)


class MembershipPackageListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        packages = membership_service.get_active_packages()
        return Response(MembershipPackageSerializer(packages, many=True, context={"request": request}).data)


class MembershipCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            membership = create_membership.execute(request.user, request.data.get("package"))
        except GymException as exc:
            return error_response(exc)
        return Response(
            UserMembershipSerializer(membership, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class MyMembershipsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = membership_service.get_my_memberships(request.user)
        return Response(UserMembershipSerializer(memberships, many=True, context={"request": request}).data)


class MembershipCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, membership_id):
        try:
            membership = membership_service.cancel_membership(request.user, membership_id)
        except GymException as exc:
            return error_response(exc)
        return Response(UserMembershipSerializer(membership, context={"request": request}).data)


class PaymentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payment = create_payment.execute(
                request.user,
                serializer.validated_data["membership"].id,
                serializer.validated_data["payment_method"],
            )
        except GymException as exc:
            return error_response(exc)
        return Response(PaymentSerializer(payment, context={"request": request}).data, status=status.HTTP_201_CREATED)


class MyPaymentsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = payment_service.get_my_payments(request.user)
        return Response(PaymentSerializer(payments, many=True, context={"request": request}).data)


class PaymentConfirmAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_id):
        from gym_booking_backend.infrastructure.models import Payment

        payment_obj = Payment.objects.filter(id=payment_id).first()
        if not payment_obj:
            return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        is_admin = hasattr(request.user, "profile") and request.user.profile.role == "admin"
        if payment_obj.user_id != request.user.id and not is_admin:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        try:
            payment = payment_service.confirm_payment(payment_id)
        except GymException as exc:
            return error_response(exc)
        return Response(PaymentSerializer(payment, context={"request": request}).data)


class TrainerBookingPaymentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        payment_method = request.data.get("payment_method", "")
        if not payment_method:
            return Response({"message": "payment_method is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = payment_service.create_trainer_booking_payment(
                user=request.user,
                trainer_booking_id=booking_id,
                payment_method=payment_method,
            )
        except GymException as exc:
            return error_response(exc)

        return Response(PaymentSerializer(payment, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ReviewCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            review = create_review.execute(
                user=request.user,
                trainer_id=data["trainer"].id if data.get("trainer") else None,
                gym_class_id=data["gym_class"].id if data.get("gym_class") else None,
                rating=data.get("rating"),
                comment=data.get("comment", ""),
            )
        except GymException as exc:
            return error_response(exc)
        return Response(ReviewSerializer(review, context={"request": request}).data, status=status.HTTP_201_CREATED)


class TrainerReviewsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, trainer_id):
        reviews = review_service.get_reviews_by_trainer(trainer_id)
        return Response(ReviewSerializer(reviews, many=True, context={"request": request}).data)


class ClassReviewsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, class_id):
        reviews = review_service.get_reviews_by_class(class_id)
        return Response(ReviewSerializer(reviews, many=True, context={"request": request}).data)


class AdminBookingListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        from gym_booking_backend.infrastructure.models import Booking
        bookings = Booking.objects.select_related("user__profile", "schedule__gym_class", "schedule__trainer", "schedule__room").all()
        return Response(BookingSerializer(bookings, many=True, context={"request": request}).data)


class AdminBookingStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        from gym_booking_backend.infrastructure.models import Booking
        from gym_booking_backend.domain.constants import BookingStatus, ScheduleStatus
        booking = Booking.objects.filter(id=booking_id).first()
        if not booking:
            return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)
        
        new_status = request.data.get("status")
        if new_status not in BookingStatus.values:
            return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)
        
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
        return Response(BookingSerializer(booking, context={"request": request}).data)


class AdminScheduleBookingListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, schedule_id):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        from gym_booking_backend.infrastructure.models import Booking, ClassSchedule

        schedule = ClassSchedule.objects.filter(id=schedule_id).first()
        if not schedule:
            return Response({"detail": "Schedule not found."}, status=status.HTTP_404_NOT_FOUND)

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
        return Response(data)


class AdminTrainerMonthlyBookingListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        bookings = booking_service.get_admin_trainer_monthly_bookings()
        return Response(TrainerMonthlyBookingSerializer(bookings, many=True, context={"request": request}).data)


class AdminTrainerMonthlyBookingStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        try:
            booking = booking_service.update_admin_trainer_monthly_booking_status(booking_id, request.data.get("status"))
        except GymException as exc:
            return error_response(exc)
        return Response(TrainerMonthlyBookingSerializer(booking, context={"request": request}).data)


class AdminPaymentListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        from gym_booking_backend.infrastructure.models import Payment
        payments = Payment.objects.select_related("user__profile", "membership__package").all()
        return Response(PaymentSerializer(payments, many=True, context={"request": request}).data)


class AdminPaymentConfirmAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_id):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        try:
            payment = payment_service.confirm_payment(payment_id)
        except GymException as exc:
            return error_response(exc)
        return Response(PaymentSerializer(payment, context={"request": request}).data)


class TrainerScheduleListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "trainer":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        from gym_booking_backend.infrastructure.models import Trainer, ClassSchedule
        trainer = Trainer.objects.filter(user=request.user).first()
        if not trainer:
            return Response({"detail": "Trainer profile not linked to user."}, status=status.HTTP_404_NOT_FOUND)
        schedules = ClassSchedule.objects.select_related("gym_class", "trainer", "room").filter(trainer=trainer)
        return Response(ClassScheduleSerializer(schedules, many=True, context={"request": request}).data)


class TrainerScheduleBookingListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, schedule_id):
        if not hasattr(request.user, "profile") or request.user.profile.role != "trainer":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        from gym_booking_backend.infrastructure.models import Trainer, ClassSchedule, Booking
        trainer = Trainer.objects.filter(user=request.user).first()
        if not trainer:
            return Response({"detail": "Trainer profile not linked to user."}, status=status.HTTP_404_NOT_FOUND)
        
        schedule = ClassSchedule.objects.filter(id=schedule_id, trainer=trainer).first()
        if not schedule:
            return Response({"detail": "Schedule not found or does not belong to you."}, status=status.HTTP_404_NOT_FOUND)
            
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
        return Response(data)


class TrainerPersonalBookingListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            bookings = booking_service.get_trainer_personal_bookings(request.user)
        except GymException as exc:
            return error_response(exc, status.HTTP_404_NOT_FOUND)
        return Response(TrainerBookingSerializer(bookings, many=True, context={"request": request}).data)


class TrainerPersonalBookingStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        new_status = request.data.get("status")
        try:
            booking = booking_service.update_trainer_booking_status(request.user, booking_id, new_status)
        except GymException as exc:
            return error_response(exc)
        return Response(TrainerBookingSerializer(booking, context={"request": request}).data)


class TrainerMonthlyBookingListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            bookings = booking_service.get_trainer_monthly_bookings(request.user)
        except GymException as exc:
            return error_response(exc, status.HTTP_404_NOT_FOUND)
        return Response(TrainerMonthlyBookingSerializer(bookings, many=True, context={"request": request}).data)


class TrainerMonthlyBookingStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        try:
            booking = booking_service.update_trainer_monthly_booking_status(request.user, booking_id, request.data.get("status"))
        except GymException as exc:
            return error_response(exc)
        return Response(TrainerMonthlyBookingSerializer(booking, context={"request": request}).data)


class TrainerBookingAttendanceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        if not hasattr(request.user, "profile") or request.user.profile.role != "trainer":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        from gym_booking_backend.infrastructure.models import Trainer, Booking
        trainer = Trainer.objects.filter(user=request.user).first()
        if not trainer:
            return Response({"detail": "Trainer profile not linked to user."}, status=status.HTTP_404_NOT_FOUND)

        booking = Booking.objects.filter(id=booking_id, schedule__trainer=trainer).first()
        if not booking:
            return Response({"detail": "Booking not found or does not belong to your schedule."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("status")
        if new_status not in ["completed", "no_show"]:
            return Response({"detail": "Invalid status for attendance."}, status=status.HTTP_400_BAD_REQUEST)

        booking.status = new_status
        booking.save(update_fields=["status"])

        return Response(BookingSerializer(booking, context={"request": request}).data)


class MembershipFreezeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, membership_id):
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        reason = request.data.get("reason", "")

        if not start_date or not end_date:
            return Response({"detail": "start_date and end_date are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            freeze = membership_service.freeze_membership(
                user=request.user,
                membership_id=membership_id,
                start_date=start_date,
                end_date=end_date,
                reason=reason
            )
        except GymException as exc:
            return error_response(exc)

        from gym_booking_backend.presentation.serializers import MembershipFreezeSerializer
        return Response(MembershipFreezeSerializer(freeze, context={"request": request}).data, status=status.HTTP_201_CREATED)


class MyInvoicesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from gym_booking_backend.infrastructure.models import Invoice
        invoices = Invoice.objects.filter(user=request.user)
        from gym_booking_backend.presentation.serializers import InvoiceSerializer
        return Response(InvoiceSerializer(invoices, many=True, context={"request": request}).data)


class InvoiceDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, invoice_id):
        from gym_booking_backend.infrastructure.models import Invoice
        invoice = Invoice.objects.filter(id=invoice_id, user=request.user).first()
        if not invoice:
            return Response({"detail": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)
        from gym_booking_backend.presentation.serializers import InvoiceSerializer
        return Response(InvoiceSerializer(invoice, context={"request": request}).data)


class TrainerReviewsListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "trainer":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        from gym_booking_backend.infrastructure.models import Trainer, Review
        trainer = Trainer.objects.filter(user=request.user).first()
        if not trainer:
            return Response({"detail": "Trainer profile not linked to user."}, status=status.HTTP_404_NOT_FOUND)
        reviews = Review.objects.filter(trainer=trainer)
        from gym_booking_backend.presentation.serializers import ReviewSerializer
        return Response(ReviewSerializer(reviews, many=True, context={"request": request}).data)


class AdminInvoiceListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        from gym_booking_backend.infrastructure.models import Invoice
        invoices = Invoice.objects.select_related("user__profile").all()
        from gym_booking_backend.presentation.serializers import InvoiceSerializer
        return Response(InvoiceSerializer(invoices, many=True, context={"request": request}).data)


class AdminCreateScheduleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        from django.core.exceptions import ValidationError
        from gym_booking_backend.presentation.serializers import ClassScheduleSerializer
        serializer = ClassScheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            schedule = serializer.save()
        except ValidationError as exc:
            return Response({"message": str(exc.message_dict if hasattr(exc, 'message_dict') else exc.messages)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return error_response(exc)

        return Response(ClassScheduleSerializer(schedule, context={"request": request}).data, status=status.HTTP_201_CREATED)


class AdminScheduleDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _require_admin(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        return None

    def patch(self, request, schedule_id):
        deny = self._require_admin(request)
        if deny:
            return deny

        from django.core.exceptions import ValidationError
        from gym_booking_backend.infrastructure.models import ClassSchedule

        schedule = ClassSchedule.objects.filter(id=schedule_id).first()
        if not schedule:
            return Response({"detail": "Schedule not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ClassScheduleSerializer(schedule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            schedule = serializer.save()
        except ValidationError as exc:
            return Response({"message": str(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return error_response(exc)

        return Response(ClassScheduleSerializer(schedule, context={"request": request}).data)

    def delete(self, request, schedule_id):
        deny = self._require_admin(request)
        if deny:
            return deny

        from gym_booking_backend.infrastructure.models import ClassSchedule

        schedule = ClassSchedule.objects.filter(id=schedule_id).first()
        if not schedule:
            return Response({"detail": "Schedule not found."}, status=status.HTTP_404_NOT_FOUND)

        schedule.delete()
        return Response({"message": "Deleted schedule successfully."})


class AdminCreateUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        username = request.data.get("username", "").strip()
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")
        full_name = request.data.get("full_name", "").strip()
        phone = request.data.get("phone", "").strip()
        role = request.data.get("role", "member")

        if not username or not password:
            return Response({"message": "Tên đăng nhập và mật khẩu là bắt buộc."}, status=status.HTTP_400_BAD_REQUEST)

        if role not in ("member", "trainer"):
            return Response({"message": "Vai trò phải là 'member' hoặc 'trainer'."}, status=status.HTTP_400_BAD_REQUEST)

        from django.contrib.auth.models import User
        if User.objects.filter(username=username).exists():
            return Response({"message": f"Tên đăng nhập '{username}' đã tồn tại."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            first_name = full_name.split(" ", 1)[0] if full_name else ""
            last_name = full_name.split(" ", 1)[1] if " " in full_name else ""

            user = register_user.execute(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role,
            )

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

            return Response({
                "message": f"Tạo tài khoản '{username}' thành công với vai trò {'Hội viên' if role == 'member' else 'Huấn luyện viên'}.",
                "id": user.id,
                "username": user.username,
                "role": role,
            }, status=status.HTTP_201_CREATED)
        except GymException as exc:
            return error_response(exc)


class AdminCreateGymClassAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        from gym_booking_backend.infrastructure.models import GymClass, Category, Trainer as TrainerModel

        name = request.data.get("name", "").strip()
        category_id = request.data.get("category")
        trainer_id = request.data.get("trainer")
        description = request.data.get("description", "")
        difficulty_level = request.data.get("difficulty_level", "beginner")
        duration_minutes = request.data.get("duration_minutes", 60)
        price = request.data.get("price", 0)

        if not name or not category_id or not trainer_id:
            return Response({"message": "Tên lớp, danh mục và HLV là bắt buộc."}, status=status.HTTP_400_BAD_REQUEST)

        category = Category.objects.filter(id=category_id).first()
        if not category:
            return Response({"message": "Danh mục không tồn tại."}, status=status.HTTP_400_BAD_REQUEST)

        trainer = TrainerModel.objects.filter(id=trainer_id).first()
        if not trainer:
            return Response({"message": "Huấn luyện viên không tồn tại."}, status=status.HTTP_400_BAD_REQUEST)

        if GymClass.objects.filter(name=name).exists():
            return Response({"message": f"Lớp tập '{name}' đã tồn tại."}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response(
                GymClassSerializer(gym_class, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            return error_response(exc)


class AdminCreatePackageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        from gym_booking_backend.infrastructure.models import MembershipPackage

        name = request.data.get("name", "").strip()
        description = request.data.get("description", "")
        price = request.data.get("price")
        duration_days = request.data.get("duration_days")

        if not name or not price or not duration_days:
            return Response({"message": "Tên gói, giá và số ngày là bắt buộc."}, status=status.HTTP_400_BAD_REQUEST)

        if MembershipPackage.objects.filter(name=name).exists():
            return Response({"message": f"Gói tập '{name}' đã tồn tại."}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response(
                MembershipPackageSerializer(package, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            return error_response(exc)


class AdminPackageDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _require_admin(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        return None

    def patch(self, request, package_id):
        deny = self._require_admin(request)
        if deny:
            return deny

        from gym_booking_backend.infrastructure.models import MembershipPackage

        package = MembershipPackage.objects.filter(id=package_id).first()
        if not package:
            return Response({"detail": "Package not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = MembershipPackageSerializer(package, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        package = serializer.save()
        return Response(MembershipPackageSerializer(package, context={"request": request}).data)

    def delete(self, request, package_id):
        deny = self._require_admin(request)
        if deny:
            return deny

        from gym_booking_backend.infrastructure.models import MembershipPackage

        package = MembershipPackage.objects.filter(id=package_id).first()
        if not package:
            return Response({"detail": "Package not found."}, status=status.HTTP_404_NOT_FOUND)

        package.delete()
        return Response({"message": "Deleted package successfully."})


class AdminTrainerListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _require_admin(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        return None

    def get(self, request):
        deny = self._require_admin(request)
        if deny:
            return deny
        from gym_booking_backend.infrastructure.models import Trainer
        trainers = Trainer.objects.all()
        return Response(TrainerSerializer(trainers, many=True, context={"request": request}).data)

    def post(self, request):
        deny = self._require_admin(request)
        if deny:
            return deny
        serializer = TrainerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trainer = serializer.save()
        return Response(TrainerSerializer(trainer, context={"request": request}).data, status=status.HTTP_201_CREATED)


class AdminTrainerDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _require_admin(self, request):
        if not hasattr(request.user, "profile") or request.user.profile.role != "admin":
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        return None

    def patch(self, request, trainer_id):
        deny = self._require_admin(request)
        if deny:
            return deny

        from gym_booking_backend.infrastructure.models import Trainer

        trainer = Trainer.objects.filter(id=trainer_id).first()
        if not trainer:
            return Response({"detail": "Trainer not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = TrainerSerializer(trainer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        trainer = serializer.save()
        return Response(TrainerSerializer(trainer, context={"request": request}).data)

    def delete(self, request, trainer_id):
        deny = self._require_admin(request)
        if deny:
            return deny

        from django.db.models import ProtectedError
        from gym_booking_backend.infrastructure.models import Trainer

        trainer = Trainer.objects.filter(id=trainer_id).first()
        if not trainer:
            return Response({"detail": "Trainer not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            trainer.delete()
        except ProtectedError:
            return Response(
                {"message": "Cannot delete trainer because it is still linked to class or schedule."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"message": "Deleted trainer successfully."})
