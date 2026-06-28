from datetime import datetime
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from gym_booking_backend.presentation.views import BaseAPIView

from gym_booking_backend.infrastructure.models import PTPackage, UserPTPackage, PTBooking, TrainerSchedule
from gym_booking_backend.application.services.pt_booking_service import pt_booking_service
from gym_booking_backend.domain.constants import WeekdayChoices, UserPTPackageStatus


class PTPackageListAPIView(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        packages = PTPackage.objects.filter(is_active=True)
        user = request.user
        has_active_membership = False
        has_active_pt_package = False

        if user.is_authenticated:
            from gym_booking_backend.infrastructure.repositories.membership_repository import membership_repository
            has_active_membership = membership_repository.has_active_membership(user)
            has_active_pt_package = UserPTPackage.objects.filter(
                user=user, status=UserPTPackageStatus.ACTIVE
            ).exists()

        from gym_booking_backend.presentation.serializers import PTPackageSerializer
        serialized_packages = PTPackageSerializer(packages, many=True).data
        return Response({
            "packages": serialized_packages,
            "has_active_membership": has_active_membership,
            "has_active_pt_package": has_active_pt_package
        }, status=status.HTTP_200_OK)


class MonthlyPTBookingCreateAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from gym_booking_backend.presentation.serializers import MonthlyPTBookingCreateSerializer, UserPTPackageSerializer
        
        # Check active membership
        from gym_booking_backend.infrastructure.repositories.membership_repository import membership_repository
        if not membership_repository.has_active_membership(request.user):
            return Response({"message": "Bạn cần đăng ký thẻ hội viên gym còn hạn để đặt gói tập PT."}, status=status.HTTP_400_BAD_REQUEST)

        # Check existing active PT packages
        if UserPTPackage.objects.filter(user=request.user, status=UserPTPackageStatus.ACTIVE).exists():
            return Response({"message": "Bạn hiện tại đang có gói tập PT đang hoạt động."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = MonthlyPTBookingCreateSerializer(data=request.data)
        if not serializer.is_valid():
            # Join validation errors into a friendly message
            err_msg = ""
            for field, errors in serializer.errors.items():
                err_msg += f"{field}: {', '.join(errors)}. "
            return Response({"message": err_msg.strip()}, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        result = pt_booking_service.create_monthly_pt_bookings(
            user=request.user,
            package_id=validated_data["package"],
            trainer_id=validated_data["trainer"],
            start_date=validated_data["start_date"],
            selected_weekdays=validated_data["weekdays"],
            start_time=validated_data["start_time"],
            end_time=validated_data["end_time"],
            note=validated_data["note"]
        )

        if not result.success:
            resp_data = {"message": result.message}
            if result.data is not None:
                resp_data["detail"] = result.data
            return Response(resp_data, status=result.status_code)

        serialized_package = UserPTPackageSerializer(result.data["package"]).data
        return Response({
            "message": "Đăng ký và khởi tạo lịch tập PT thành công!",
            "package": serialized_package
        }, status=status.HTTP_201_CREATED)


class UserPTPackageListAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from gym_booking_backend.presentation.serializers import UserPTPackageSerializer
        packages = UserPTPackage.objects.select_related("trainer", "package").filter(user=request.user)
        serialized = UserPTPackageSerializer(packages, many=True).data
        return Response(serialized, status=status.HTTP_200_OK)


class UserPTPackageDetailAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from gym_booking_backend.presentation.serializers import UserPTPackageSerializer
        try:
            package = UserPTPackage.objects.select_related("trainer", "package").get(id=pk, user=request.user)
        except UserPTPackage.DoesNotExist:
            return Response({"message": "Gói PT không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

        serialized = UserPTPackageSerializer(package).data
        return Response(serialized, status=status.HTTP_200_OK)


class CancelPTBookingAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            booking = PTBooking.objects.get(id=pk, user=request.user)
        except PTBooking.DoesNotExist:
            return Response({"message": "Buổi tập không tồn tại hoặc không thuộc quyền sở hữu của bạn."}, status=status.HTTP_404_NOT_FOUND)

        result = pt_booking_service.cancel_pt_booking(booking.id)
        if result.success:
            return Response({"message": "Đã hủy buổi tập thành công."}, status=status.HTTP_200_OK)
        return Response({"message": result.message}, status=result.status_code)


class CancelUserPTPackageAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            package = UserPTPackage.objects.get(id=pk, user=request.user)
        except UserPTPackage.DoesNotExist:
            return Response({"message": "Gói tập PT không tồn tại hoặc không thuộc quyền sở hữu của bạn."}, status=status.HTTP_404_NOT_FOUND)

        result = pt_booking_service.cancel_user_pt_package(package.id)
        if result.success:
            return Response({"message": "Đã hủy gói tập PT thành công."}, status=status.HTTP_200_OK)
        return Response({"message": result.message}, status=result.status_code)


class PTBookingPreviewAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        package_id = request.GET.get("package")
        trainer_id = request.GET.get("trainer")
        start_date_str = request.GET.get("start_date")
        weekdays_str = request.GET.get("weekdays")
        start_time_str = request.GET.get("start_time")
        end_time_str = request.GET.get("end_time")

        if not all([package_id, trainer_id, start_date_str, weekdays_str, start_time_str, end_time_str]):
            return Response({"message": "Vui lòng nhập đầy đủ thông tin để xem trước lịch tập."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            result = pt_booking_service.preview_monthly_pt_bookings(
                user=request.user,
                package_id=int(package_id),
                trainer_id=int(trainer_id),
                start_date=start_date,
                selected_weekdays=weekdays_str,
                start_time=start_time_str,
                end_time=end_time_str
            )

            if not result.success:
                resp_data = {"message": result.message}
                if result.data is not None:
                    resp_data["detail"] = result.data
                return Response(resp_data, status=result.status_code)

            data = []
            for p in result.data:
                data.append({
                    "date": p["date"].strftime("%Y-%m-%d"),
                    "weekday": dict(WeekdayChoices.choices).get(p["date"].weekday()),
                    "start_time": p["start_time"].strftime("%H:%M"),
                    "end_time": p["end_time"].strftime("%H:%M"),
                    "trainer_conflict": p["trainer_conflict"],
                    "user_conflict": p["user_conflict"],
                    "is_valid": p["is_valid"]
                })
            return Response({"sessions": data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

