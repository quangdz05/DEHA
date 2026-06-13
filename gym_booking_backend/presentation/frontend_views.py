from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from gym_booking_backend.application.services import (
    auth_service,
    booking_service,
    catalog_service,
    membership_service,
    payment_service,
    profile_service,
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
from gym_booking_backend.infrastructure.models import ClassSchedule, GymClass, Payment, Trainer, UserMembership


def home(request):
    return render(
        request,
        "home.html",
        {
            "featured_classes": catalog_service.get_classes()[:6],
            "featured_trainers": catalog_service.get_trainers()[:3],
            "packages": membership_service.get_active_packages(),
        },
    )


def register_view(request):
    if request.method == "POST":
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")
        full_name = request.POST.get("full_name", "").strip()
        first_name = full_name.split(" ", 1)[0] if full_name else ""
        last_name = full_name.split(" ", 1)[1] if " " in full_name else ""
        if password != password_confirm:
            messages.error(request, "Mat khau nhap lai khong khop.")
        else:
            try:
                user = register_user.execute(
                    username=request.POST.get("username", ""),
                    email=request.POST.get("email", ""),
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                profile_service.update_my_profile(
                    user,
                    {"full_name": full_name or user.username, "phone": request.POST.get("phone", "")},
                )
                login(request, user)
                messages.success(request, "Dang ky thanh cong.")
                return redirect("frontend:home")
            except GymException as exc:
                messages.error(request, str(exc))
    return render(request, "accounts/register.html")


def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            auth_service.login_user(request, form.cleaned_data["username"], form.cleaned_data["password"])
            messages.success(request, "Dang nhap thanh cong.")
            return redirect("frontend:home")
        messages.error(request, "Sai tai khoan hoac mat khau.")
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "Da dang xuat.")
    return redirect("frontend:home")


@login_required
def profile(request):
    return render(request, "accounts/profile.html", {"profile": profile_service.get_my_profile(request.user)})


@login_required
def profile_edit(request):
    profile_obj = profile_service.get_my_profile(request.user)
    if request.method == "POST":
        data = {
            "full_name": request.POST.get("full_name", ""),
            "phone": request.POST.get("phone", ""),
            "gender": request.POST.get("gender", ""),
            "date_of_birth": request.POST.get("date_of_birth") or None,
            "address": request.POST.get("address", ""),
        }
        if request.FILES.get("avatar"):
            data["avatar"] = request.FILES["avatar"]
        update_profile.execute(request.user, data)
        messages.success(request, "Cap nhat ho so thanh cong.")
        return redirect("frontend:profile")
    return render(request, "accounts/profile_form.html", {"profile": profile_obj})


def trainer_list(request):
    return render(request, "trainers/trainer_list.html", {"trainers": catalog_service.get_trainers()})


def trainer_detail(request, trainer_id):
    trainer = get_object_or_404(Trainer, id=trainer_id)
    return render(
        request,
        "trainers/trainer_detail.html",
        {"trainer": trainer, "classes": catalog_service.get_classes(trainer_id=trainer.id)},
    )


def class_list(request):
    classes = catalog_service.get_classes(
        category_id=request.GET.get("category") or None,
        trainer_id=request.GET.get("trainer") or None,
    )
    query = request.GET.get("q", "").strip()
    difficulty = request.GET.get("difficulty", "").strip()
    if query:
        classes = classes.filter(name__icontains=query)
    if difficulty:
        classes = classes.filter(difficulty_level=difficulty)
    return render(
        request,
        "classes/class_list.html",
        {
            "classes": classes,
            "categories": catalog_service.get_categories(),
            "trainers": catalog_service.get_trainers(),
            "selected": request.GET,
        },
    )


def class_detail(request, class_id):
    gym_class = get_object_or_404(GymClass, id=class_id)
    schedules = ClassSchedule.objects.select_related("room", "gym_class__trainer").filter(gym_class=gym_class)
    return render(
        request,
        "classes/class_detail.html",
        {"gym_class": gym_class, "schedules": schedules},
    )


def schedule_list(request):
    schedules = schedule_service.get_schedules(
        date=request.GET.get("date") or None,
        trainer_id=request.GET.get("trainer") or None,
        available=request.GET.get("available") == "on",
    )
    category_id = request.GET.get("category")
    if category_id:
        schedules = schedules.filter(gym_class__category_id=category_id)
    return render(
        request,
        "schedules/schedule_list.html",
        {
            "schedules": schedules,
            "trainers": catalog_service.get_trainers(),
            "categories": catalog_service.get_categories(),
            "selected": request.GET,
        },
    )


@login_required
def booking_confirm(request, schedule_id):
    schedule = get_object_or_404(ClassSchedule.objects.select_related("gym_class", "gym_class__trainer", "room"), id=schedule_id)
    if request.method == "POST":
        try:
            create_booking.execute(request.user, schedule.id, request.POST.get("note", ""))
            messages.success(request, "Dat lich thanh cong.")
            return redirect("frontend:my_bookings")
        except GymException as exc:
            messages.error(request, str(exc))
    return render(request, "bookings/booking_confirm.html", {"schedule": schedule})


@login_required
def my_bookings(request):
    bookings = booking_service.get_my_bookings(request.user)
    status = request.GET.get("status")
    if status:
        bookings = bookings.filter(status=status)
    return render(request, "bookings/my_bookings.html", {"bookings": bookings, "selected_status": status})


@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(booking_service.get_my_bookings(request.user), id=booking_id)
    return render(request, "bookings/booking_detail.html", {"booking": booking})


@login_required
def booking_cancel(request, booking_id):
    if request.method == "POST":
        try:
            cancel_booking.execute(request.user, booking_id)
            messages.success(request, "Da huy lich tap.")
        except GymException as exc:
            messages.error(request, str(exc))
    return redirect("frontend:my_bookings")


def package_list(request):
    return render(request, "memberships/package_list.html", {"packages": membership_service.get_active_packages()})


@login_required
def membership_create(request, package_id):
    try:
        membership = create_membership.execute(request.user, package_id)
        messages.success(request, "Dang ky goi tap thanh cong.")
        return redirect("frontend:payment_confirm", membership_id=membership.id)
    except GymException as exc:
        messages.error(request, str(exc))
        return redirect("frontend:packages")


@login_required
def my_membership(request):
    membership = membership_service.get_my_memberships(request.user).first()
    return render(request, "memberships/my_membership.html", {"membership": membership})


@login_required
def payment_confirm(request, membership_id):
    membership = get_object_or_404(UserMembership.objects.select_related("package"), id=membership_id, user=request.user)
    if request.method == "POST":
        try:
            payment = create_payment.execute(request.user, membership.id, request.POST.get("payment_method"))
            payment_service.confirm_payment(payment.id)
            messages.success(request, "Thanh toan gia lap thanh cong.")
            return redirect("frontend:payment_history")
        except GymException as exc:
            messages.error(request, str(exc))
    return render(request, "payments/payment_confirm.html", {"membership": membership})


@login_required
def payment_history(request):
    return render(request, "payments/payment_history.html", {"payments": payment_service.get_my_payments(request.user)})


@login_required
def review_form(request):
    class_id = request.GET.get("class")
    trainer_id = request.GET.get("trainer")
    gym_class = GymClass.objects.filter(id=class_id).first() if class_id else None
    trainer = Trainer.objects.filter(id=trainer_id).first() if trainer_id else None
    if request.method == "POST":
        try:
            create_review.execute(
                request.user,
                trainer_id=request.POST.get("trainer") or None,
                gym_class_id=request.POST.get("gym_class") or None,
                rating=request.POST.get("rating"),
                comment=request.POST.get("comment", ""),
            )
            messages.success(request, "Cam on ban da danh gia.")
            return redirect("frontend:home")
        except GymException as exc:
            messages.error(request, str(exc))
    return render(
        request,
        "reviews/review_form.html",
        {"gym_class": gym_class, "trainer": trainer},
    )
