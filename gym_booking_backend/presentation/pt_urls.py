from django.urls import path
from gym_booking_backend.presentation.pt_views import (
    PTPackageListView,
    MonthlyPTBookingCreateView,
    UserPTPackageListView,
    UserPTPackageDetailView,
    CancelPTBookingView,
    CancelUserPTPackageView,
    PTBookingPreviewView,
)

urlpatterns = [
    path("pt-packages/", PTPackageListView.as_view(), name="pt_package_list"),
    path("pt-booking/monthly/create/", MonthlyPTBookingCreateView.as_view(), name="monthly_pt_booking_create"),
    path("my-pt-packages/", UserPTPackageListView.as_view(), name="user_pt_package_list"),
    path("my-pt-packages/<int:pk>/", UserPTPackageDetailView.as_view(), name="user_pt_package_detail"),
    path("pt-booking/<int:pk>/cancel/", CancelPTBookingView.as_view(), name="cancel_pt_booking"),
    path("my-pt-packages/<int:pk>/cancel/", CancelUserPTPackageView.as_view(), name="cancel_user_pt_package"),
    path("pt-booking/preview/", PTBookingPreviewView.as_view(), name="pt_booking_preview"),
]
