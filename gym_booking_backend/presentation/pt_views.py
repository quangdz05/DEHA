from datetime import datetime
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy

from gym_booking_backend.infrastructure.models import PTPackage, UserPTPackage, PTBooking
from gym_booking_backend.presentation.forms import MonthlyPTBookingForm
from gym_booking_backend.application.services import pt_booking_service
from gym_booking_backend.infrastructure.repositories import membership_repository
from gym_booking_backend.domain.constants import WeekdayChoices, UserPTPackageStatus


class PTPackageListView(ListView):
    model = PTPackage
    template_name = "pt/pt_package_list.html"
    context_object_name = "packages"
    queryset = PTPackage.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        has_active_membership = False
        has_active_pt_package = False
        
        if user.is_authenticated:
            has_active_membership = membership_repository.has_active_membership(user)
            has_active_pt_package = UserPTPackage.objects.filter(
                user=user, status=UserPTPackageStatus.ACTIVE
            ).exists()
            
        context["has_active_membership"] = has_active_membership
        context["has_active_pt_package"] = has_active_pt_package
        return context


class MonthlyPTBookingCreateView(LoginRequiredMixin, FormView):
    form_class = MonthlyPTBookingForm
    template_name = "pt/monthly_pt_booking_form.html"
    login_url = "/login.html"

    def dispatch(self, request, *args, **kwargs):
        # Additional validation: User must have active membership and not already have active PT package
        if not membership_repository.has_active_membership(request.user):
            messages.error(request, "Bạn cần đăng ký thẻ hội viên gym còn hạn để đặt gói tập PT.")
            return redirect("pt_package_list")
            
        if UserPTPackage.objects.filter(user=request.user, status=UserPTPackageStatus.ACTIVE).exists():
            messages.warning(request, "Bạn hiện tại đang có gói tập PT đang hoạt động.")
            return redirect("user_pt_package_list")
            
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        package_id = self.request.GET.get("package")
        if package_id:
            package = PTPackage.objects.filter(id=package_id, is_active=True).first()
            if package:
                initial["package"] = package
        return initial

    def form_valid(self, form):
        form_data = form.cleaned_data
        try:
            user_package, bookings = pt_booking_service.create_monthly_pt_bookings(
                user=self.request.user,
                package_id=form_data["package"].id,
                trainer_id=form_data["trainer"].id,
                start_date=form_data["start_date"],
                selected_weekdays=form_data["weekdays"],
                start_time=form_data["start_time"],
                end_time=form_data["end_time"],
                note=form_data["note"],
            )
            messages.success(self.request, "Đăng ký và khởi tạo lịch tập PT thành công!")
            return redirect("user_pt_package_detail", pk=user_package.id)
        except Exception as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)


class UserPTPackageListView(LoginRequiredMixin, ListView):
    model = UserPTPackage
    template_name = "pt/user_pt_package_list.html"
    context_object_name = "user_packages"
    login_url = "/login.html"

    def get_queryset(self):
        return UserPTPackage.objects.select_related("trainer", "package").filter(user=self.request.user)


class UserPTPackageDetailView(LoginRequiredMixin, DetailView):
    model = UserPTPackage
    template_name = "pt/user_pt_package_detail.html"
    context_object_name = "user_package"
    login_url = "/login.html"

    def get_queryset(self):
        return UserPTPackage.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bookings"] = self.object.bookings.all().order_by("booking_date", "start_time")
        return context


class CancelPTBookingView(LoginRequiredMixin, View):
    login_url = "/login.html"

    def post(self, request, pk):
        try:
            booking = PTBooking.objects.get(id=pk, user=request.user)
            pt_booking_service.cancel_pt_booking(booking.id)
            messages.success(request, "Đã hủy buổi tập thành công.")
        except Exception as e:
            messages.error(request, f"Không thể hủy buổi tập: {str(e)}")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", reverse("user_pt_package_list")))


class CancelUserPTPackageView(LoginRequiredMixin, View):
    login_url = "/login.html"

    def post(self, request, pk):
        try:
            package = UserPTPackage.objects.get(id=pk, user=request.user)
            pt_booking_service.cancel_user_pt_package(package.id)
            messages.success(request, "Đã hủy gói tập PT thành công.")
        except Exception as e:
            messages.error(request, f"Không thể hủy gói tập: {str(e)}")
        return HttpResponseRedirect(reverse("user_pt_package_detail", kwargs={"pk": pk}))


class PTBookingPreviewView(LoginRequiredMixin, View):
    login_url = "/login.html"

    def get(self, request):
        package_id = request.GET.get("package")
        trainer_id = request.GET.get("trainer")
        start_date_str = request.GET.get("start_date")
        weekdays_str = request.GET.get("weekdays")
        start_time_str = request.GET.get("start_time")
        end_time_str = request.GET.get("end_time")

        if not all([package_id, trainer_id, start_date_str, weekdays_str, start_time_str, end_time_str]):
            return JsonResponse({"error": "Vui lòng nhập đầy đủ thông tin để xem trước lịch tập."}, status=400)

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            previews = pt_booking_service.preview_monthly_pt_bookings(
                user=request.user,
                package_id=int(package_id),
                trainer_id=int(trainer_id),
                start_date=start_date,
                selected_weekdays=weekdays_str,
                start_time=start_time_str,
                end_time=end_time_str
            )
            
            data = []
            for p in previews:
                data.append({
                    "date": p["date"].strftime("%Y-%m-%d"),
                    "weekday": dict(WeekdayChoices.choices).get(p["date"].weekday()),
                    "start_time": p["start_time"].strftime("%H:%M"),
                    "end_time": p["end_time"].strftime("%H:%M"),
                    "trainer_conflict": p["trainer_conflict"],
                    "user_conflict": p["user_conflict"],
                    "is_valid": p["is_valid"]
                })
            return JsonResponse({"sessions": data})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
