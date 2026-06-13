from django.contrib import admin

from .models import (
    Booking,
    Category,
    ClassSchedule,
    GymClass,
    MembershipPackage,
    Payment,
    Profile,
    Review,
    Room,
    Trainer,
    TrainerBooking,
    TrainerMonthlyBooking,
    UserMembership,
    MembershipFreeze,
    Invoice,
    InvoiceItem,
    PTPackage,
    TrainerSchedule,
    UserPTPackage,
    PTBooking,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "full_name", "phone", "gender", "created_at")
    search_fields = ("user__username", "full_name", "phone")
    list_filter = ("gender", "created_at")


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "phone", "specialty", "experience_years", "session_price", "status")
    search_fields = ("name", "email", "phone", "specialty")
    list_filter = ("status", "specialty")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "location", "capacity", "status")
    search_fields = ("name", "location")
    list_filter = ("status",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status")
    search_fields = ("name",)
    list_filter = ("status",)


@admin.register(GymClass)
class GymClassAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "trainer", "difficulty_level", "duration_minutes", "price", "status")
    search_fields = ("name", "category__name", "trainer__name")
    list_filter = ("status", "difficulty_level", "category")


@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "gym_class",
        "room",
        "trainer",
        "start_time",
        "end_time",
        "max_participants",
        "current_participants",
        "status",
    )
    search_fields = ("gym_class__name", "room__name", "gym_class__trainer__name")
    list_filter = ("status", "start_time", "room")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "booking_code", "user", "schedule", "status", "booked_at", "cancelled_at")
    search_fields = ("booking_code", "user__username", "schedule__gym_class__name")
    list_filter = ("status", "booked_at")


@admin.register(TrainerBooking)
class TrainerBookingAdmin(admin.ModelAdmin):
    list_display = ("id", "booking_code", "user", "trainer", "start_time", "end_time", "status", "booked_at")
    search_fields = ("booking_code", "user__username", "trainer__name")
    list_filter = ("status", "start_time", "trainer")


@admin.register(TrainerMonthlyBooking)
class TrainerMonthlyBookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "booking_code",
        "user",
        "trainer",
        "start_date",
        "end_date",
        "months",
        "sessions_per_week",
        "status",
    )
    search_fields = ("booking_code", "user__username", "trainer__name")
    list_filter = ("status", "start_date", "trainer")


@admin.register(MembershipPackage)
class MembershipPackageAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "duration_days", "max_bookings_per_week", "status")
    search_fields = ("name",)
    list_filter = ("status",)


@admin.register(UserMembership)
class UserMembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "package", "start_date", "end_date", "status", "created_at")
    search_fields = ("user__username", "package__name")
    list_filter = ("status", "start_date", "end_date")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "membership", "invoice", "amount", "payment_method", "status", "paid_at", "created_at")
    search_fields = ("user__username", "transaction_code", "membership__package__name", "invoice__invoice_number")
    list_filter = ("status", "payment_method", "created_at")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "trainer", "gym_class", "rating", "created_at")
    search_fields = ("user__username", "trainer__name", "gym_class__name", "comment")
    list_filter = ("rating", "created_at")


@admin.register(MembershipFreeze)
class MembershipFreezeAdmin(admin.ModelAdmin):
    list_display = ("id", "user_membership", "start_date", "end_date", "duration_days", "created_at")
    search_fields = ("user_membership__user__username", "reason")
    list_filter = ("start_date", "end_date")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "invoice_number", "user", "total_amount", "status", "created_at")
    search_fields = ("invoice_number", "user__username")
    list_filter = ("status", "created_at")


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ("id", "invoice", "item_type", "amount")
    search_fields = ("invoice__invoice_number", "item_type")
    list_filter = ("item_type",)


@admin.register(PTPackage)
class PTPackageAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "duration_days", "total_sessions", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(TrainerSchedule)
class TrainerScheduleAdmin(admin.ModelAdmin):
    list_display = ("id", "trainer", "weekday", "start_time", "end_time", "is_available")
    search_fields = ("trainer__name",)
    list_filter = ("weekday", "is_available")


@admin.register(UserPTPackage)
class UserPTPackageAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "trainer", "package", "start_date", "end_date", "status")
    search_fields = ("user__username", "trainer__name", "package__name")
    list_filter = ("status", "start_date")


@admin.register(PTBooking)
class PTBookingAdmin(admin.ModelAdmin):
    list_display = ("id", "booking_code", "user", "trainer", "booking_date", "start_time", "end_time", "status")
    search_fields = ("booking_code", "user__username", "trainer__name")
    list_filter = ("status", "booking_date")
