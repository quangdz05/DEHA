from django.urls import path

from gym_booking_backend.presentation import frontend_views

app_name = "frontend"

urlpatterns = [
    path("", frontend_views.home, name="home"),
    path("login/", frontend_views.login_view, name="login"),
    path("logout/", frontend_views.logout_view, name="logout"),
    path("register/", frontend_views.register_view, name="register"),
    path("profile/", frontend_views.profile, name="profile"),
    path("profile/edit/", frontend_views.profile_edit, name="profile_edit"),
    path("trainers/", frontend_views.trainer_list, name="trainers"),
    path("trainers/<int:trainer_id>/", frontend_views.trainer_detail, name="trainer_detail"),
    path("classes/", frontend_views.class_list, name="classes"),
    path("classes/<int:class_id>/", frontend_views.class_detail, name="class_detail"),
    path("schedules/", frontend_views.schedule_list, name="schedules"),
    path("bookings/<int:schedule_id>/confirm/", frontend_views.booking_confirm, name="booking_confirm"),
    path("my-bookings/", frontend_views.my_bookings, name="my_bookings"),
    path("my-bookings/<int:booking_id>/", frontend_views.booking_detail, name="booking_detail"),
    path("my-bookings/<int:booking_id>/cancel/", frontend_views.booking_cancel, name="booking_cancel"),
    path("packages/", frontend_views.package_list, name="packages"),
    path("packages/<int:package_id>/register/", frontend_views.membership_create, name="membership_create"),
    path("my-membership/", frontend_views.my_membership, name="my_membership"),
    path("payments/<int:membership_id>/confirm/", frontend_views.payment_confirm, name="payment_confirm"),
    path("payments/history/", frontend_views.payment_history, name="payment_history"),
    path("reviews/new/", frontend_views.review_form, name="review_form"),
]
