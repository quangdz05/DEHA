from django.urls import path

from gym_booking_backend.presentation.chatbot import ChatbotAPIView
from gym_booking_backend.presentation import views, jwt_views, password_reset_views, two_factor_views, pt_views

urlpatterns = [
    path("chat", ChatbotAPIView.as_view(), name="chatbot-chat-no-slash"),
    path("chat/", ChatbotAPIView.as_view(), name="chatbot-chat"),
    path("auth/register/", views.RegisterAPIView.as_view(), name="auth-register"),
    path("auth/login/", jwt_views.LoginAPIView.as_view(), name="auth-login"),
    path("auth/logout/", jwt_views.LogoutAPIView.as_view(), name="auth-logout"),
    path("auth/refresh/", jwt_views.TokenRefreshAPIView.as_view(), name="auth-token-refresh"),
    
    # 2FA endpoints
    path("auth/2fa/setup/", two_factor_views.TwoFactorSetupAPIView.as_view(), name="auth-2fa-setup"),
    path("auth/2fa/enable/", two_factor_views.TwoFactorEnableAPIView.as_view(), name="auth-2fa-enable"),
    path("auth/2fa/disable/", two_factor_views.TwoFactorDisableAPIView.as_view(), name="auth-2fa-disable"),
    path("auth/2fa/verify/", two_factor_views.TwoFactorVerifyAPIView.as_view(), name="auth-2fa-verify"),
    
    # Password Reset endpoints
    path("auth/forgot-password/", password_reset_views.ForgotPasswordAPIView.as_view(), name="auth-forgot-password"),
    path("auth/reset-password/", password_reset_views.ResetPasswordAPIView.as_view(), name="auth-reset-password"),

    path("profile/me/", views.ProfileMeAPIView.as_view(), name="profile-me"),
    path("trainers/", views.TrainerListAPIView.as_view(), name="trainer-list"),
    path("trainers/schedule/", views.TrainerScheduleDetailAPIView.as_view(), name="trainer-schedule-detail-api"),
    path("trainers/<int:trainer_id>/", views.TrainerDetailAPIView.as_view(), name="trainer-detail"),
    path("trainers/<int:trainer_id>/reviews/", views.TrainerReviewsAPIView.as_view(), name="trainer-reviews"),
    path("categories/", views.CategoryListAPIView.as_view(), name="category-list"),
    path("rooms/", views.RoomListAPIView.as_view(), name="room-list"),
    path("classes/", views.GymClassListAPIView.as_view(), name="class-list"),
    path("classes/<int:class_id>/", views.GymClassDetailAPIView.as_view(), name="class-detail"),
    path("classes/<int:class_id>/reviews/", views.ClassReviewsAPIView.as_view(), name="class-reviews"),
    path("schedules/", views.ScheduleListAPIView.as_view(), name="schedule-list"),
    path("schedules/<int:schedule_id>/", views.ScheduleDetailAPIView.as_view(), name="schedule-detail"),
    path("schedules/<int:schedule_id>/assign/", views.ScheduleAssignTrainerAPIView.as_view(), name="schedule-assign-trainer"),
    path("bookings/", views.BookingCreateAPIView.as_view(), name="booking-create"),
    path("bookings/my/", views.MyBookingsAPIView.as_view(), name="booking-my"),
    path("bookings/<int:booking_id>/cancel/", views.BookingCancelAPIView.as_view(), name="booking-cancel"),
    path("trainer-bookings/", views.TrainerBookingCreateAPIView.as_view(), name="trainer-booking-create"),
    path("trainer-bookings/my/", views.MyTrainerBookingsAPIView.as_view(), name="trainer-booking-my"),
    path("trainer-bookings/<int:booking_id>/payments/", views.TrainerBookingPaymentCreateAPIView.as_view(), name="trainer-booking-payment-create"),
    path("trainer-bookings/<int:booking_id>/cancel/", views.TrainerBookingCancelAPIView.as_view(), name="trainer-booking-cancel"),
    path("membership-packages/", views.MembershipPackageListAPIView.as_view(), name="membership-package-list"),
    path("memberships/", views.MembershipCreateAPIView.as_view(), name="membership-create"),
    path("memberships/my/", views.MyMembershipsAPIView.as_view(), name="membership-my"),
    path("memberships/<int:membership_id>/cancel/", views.MembershipCancelAPIView.as_view(), name="membership-cancel"),
    path("payments/", views.PaymentCreateAPIView.as_view(), name="payment-create"),
    path("payments/my/", views.MyPaymentsAPIView.as_view(), name="payment-my"),
    path("payments/<int:payment_id>/confirm/", views.PaymentConfirmAPIView.as_view(), name="payment-confirm"),
    path("reviews/", views.ReviewCreateAPIView.as_view(), name="review-create"),
    # Dashboard admin and trainer views
    path("admin/bookings/", views.AdminBookingListAPIView.as_view(), name="admin-bookings"),
    path("admin/bookings/<int:booking_id>/status/", views.AdminBookingStatusAPIView.as_view(), name="admin-booking-status"),
    path("admin/schedules/<int:schedule_id>/bookings/", views.AdminScheduleBookingListAPIView.as_view(), name="admin-schedule-bookings"),
    path("admin/payments/", views.AdminPaymentListAPIView.as_view(), name="admin-payments"),
    path("admin/payments/<int:payment_id>/confirm/", views.AdminPaymentConfirmAPIView.as_view(), name="admin-payment-confirm"),
    path("trainer/schedules/", views.TrainerScheduleListAPIView.as_view(), name="trainer-schedules"),
    path("trainer/schedules/<int:schedule_id>/bookings/", views.TrainerScheduleBookingListAPIView.as_view(), name="trainer-schedule-bookings"),
    path("trainer/personal-bookings/", views.TrainerPersonalBookingListAPIView.as_view(), name="trainer-personal-bookings"),
    path("trainer/personal-bookings/<int:booking_id>/status/", views.TrainerPersonalBookingStatusAPIView.as_view(), name="trainer-personal-booking-status"),
    path("trainer/bookings/<int:booking_id>/attendance/", views.TrainerBookingAttendanceAPIView.as_view(), name="trainer-booking-attendance"),
    path("memberships/<int:membership_id>/freeze/", views.MembershipFreezeAPIView.as_view(), name="membership-freeze"),
    path("invoices/my/", views.MyInvoicesAPIView.as_view(), name="invoices-my"),
    path("invoices/<int:invoice_id>/", views.InvoiceDetailAPIView.as_view(), name="invoice-detail"),
    path("trainer/reviews/", views.TrainerReviewsListAPIView.as_view(), name="trainer-reviews-list"),
    path("admin/invoices/", views.AdminInvoiceListAPIView.as_view(), name="admin-invoices"),
    path("admin/schedules/create/", views.AdminCreateScheduleAPIView.as_view(), name="admin-schedule-create"),
    path("admin/schedules/<int:schedule_id>/", views.AdminScheduleDetailAPIView.as_view(), name="admin-schedule-detail"),
    path("admin/users/create/", views.AdminCreateUserAPIView.as_view(), name="admin-user-create"),
    path("admin/trainers/", views.AdminTrainerListCreateAPIView.as_view(), name="admin-trainer-list-create"),
    path("admin/trainers/<int:trainer_id>/", views.AdminTrainerDetailAPIView.as_view(), name="admin-trainer-detail"),
    path("admin/classes/create/", views.AdminCreateGymClassAPIView.as_view(), name="admin-class-create"),
    path("admin/packages/create/", views.AdminCreatePackageAPIView.as_view(), name="admin-package-create"),
    path("admin/packages/<int:package_id>/", views.AdminPackageDetailAPIView.as_view(), name="admin-package-detail"),
    
    # PT REST APIs
    path("pt-packages/", pt_views.PTPackageListAPIView.as_view(), name="api-pt-package-list"),
    path("pt-booking/monthly/create/", pt_views.MonthlyPTBookingCreateAPIView.as_view(), name="api-monthly-pt-booking-create"),
    path("my-pt-packages/", pt_views.UserPTPackageListAPIView.as_view(), name="api-user-pt-package-list"),
    path("my-pt-packages/<int:pk>/", pt_views.UserPTPackageDetailAPIView.as_view(), name="api-user-pt-package-detail"),
    path("pt-booking/<int:pk>/cancel/", pt_views.CancelPTBookingAPIView.as_view(), name="api-cancel-pt-booking"),
    path("my-pt-packages/<int:pk>/cancel/", pt_views.CancelUserPTPackageAPIView.as_view(), name="api-cancel-user-pt-package"),
    path("pt-booking/preview/", pt_views.PTBookingPreviewAPIView.as_view(), name="api-pt-booking-preview"),
]


