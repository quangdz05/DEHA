from django.contrib import admin

from .models import (
    MembershipPackage,
    Payment,
    Profile,
    Review,
    Room,
    Trainer,
    TrainerBooking,
    UserMembership,
    MembershipFreeze,
    Invoice,
    InvoiceItem,
    TrainerSchedule,
    UserPTPackage,
    PTBooking,
    EmailSetting,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "full_name", "phone", "gender", "two_factor_enabled", "created_at")
    search_fields = ("user__username", "full_name", "phone")
    list_filter = ("gender", "two_factor_enabled", "created_at")


# VĐ #12: Thêm is_deleted vào list_filter cho các model SoftDelete
@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "phone", "specialty", "experience_years", "session_price", "status", "is_deleted")
    search_fields = ("name", "email", "phone", "specialty")
    list_filter = ("status", "specialty", "is_deleted")

    def get_queryset(self, request):
        """Hiển thị tất cả bản ghi trong Admin, kể cả đã xóa mềm."""
        return self.model.all_objects.all()


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "location", "capacity", "status", "is_deleted")
    search_fields = ("name", "location")
    list_filter = ("status", "is_deleted")

    def get_queryset(self, request):
        return self.model.all_objects.all()





@admin.register(TrainerBooking)
class TrainerBookingAdmin(admin.ModelAdmin):
    list_display = ("id", "booking_code", "user", "trainer", "start_time", "end_time", "status", "created_at")
    search_fields = ("booking_code", "user__username", "trainer__name")
    list_filter = ("status", "start_time", "trainer")


# TrainerMonthlyBookingAdmin removed


@admin.register(MembershipPackage)
class MembershipPackageAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "duration_days", "max_bookings_per_week", "status", "is_deleted")
    search_fields = ("name",)
    list_filter = ("status", "is_deleted")

    def get_queryset(self, request):
        return self.model.all_objects.all()


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
    list_display = ("id", "user", "trainer", "rating", "created_at")
    search_fields = ("user__username", "trainer__name", "comment")
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
    list_display = ("id", "invoice", "item_type", "content_type", "object_id", "amount")
    search_fields = ("invoice__invoice_number", "item_type")
    list_filter = ("item_type",)


# PTPackageAdmin removed


@admin.register(TrainerSchedule)
class TrainerScheduleAdmin(admin.ModelAdmin):
    list_display = ("id", "trainer", "weekday", "start_time", "end_time", "is_available")
    search_fields = ("trainer__name",)
    list_filter = ("weekday", "is_available")


@admin.register(UserPTPackage)
class UserPTPackageAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "trainer", "start_date", "end_date", "status")
    search_fields = ("user__username", "trainer__name")
    list_filter = ("status", "start_date")


@admin.register(PTBooking)
class PTBookingAdmin(admin.ModelAdmin):
    list_display = ("id", "booking_code", "user", "trainer", "booking_date", "start_time", "end_time", "status")
    search_fields = ("booking_code", "user__username", "trainer__name")
    list_filter = ("status", "booking_date")


@admin.register(EmailSetting)
class EmailSettingAdmin(admin.ModelAdmin):
    list_display = ("id", "email_host_user", "email_host", "email_port", "email_use_tls", "is_active", "updated_at")
    list_filter = ("is_active", "email_use_tls")
    search_fields = ("email_host_user", "email_host")
