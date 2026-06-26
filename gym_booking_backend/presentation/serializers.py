from django.contrib.auth.models import User
from rest_framework import serializers

from gym_booking_backend.infrastructure.models import (
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
    UserPTPackage,
    PTBooking,
    TrainerSchedule,
)


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.CharField(required=False, default="member")

    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name", "role")


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "username",
            "email",
            "full_name",
            "phone",
            "gender",
            "date_of_birth",
            "address",
            "avatar",
            "role",
            "emergency_contact_name",
            "emergency_contact_phone",
            "health_notes",
            "fitness_goals",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "username", "email", "role", "created_at", "updated_at")


class TrainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainer
        # VĐ #11: Không expose user, email, phone ra API public
        fields = (
            "id", "name", "specialty", "experience_years", "bio",
            "certifications", "session_price", "image", "status",
        )


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class GymClassSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    trainer_name = serializers.CharField(source="trainer.name", read_only=True)

    class Meta:
        model = GymClass
        fields = (
            "id",
            "category",
            "category_name",
            "trainer",
            "trainer_name",
            "name",
            "description",
            "difficulty_level",
            "duration_minutes",
            "price",
            "image",
            "status",
            "created_at",
            "updated_at",
        )


class ClassScheduleSerializer(serializers.ModelSerializer):
    gym_class_name = serializers.CharField(source="gym_class.name", read_only=True)
    trainer_name = serializers.CharField(source="trainer.name", read_only=True)
    room_name = serializers.CharField(source="room.name", read_only=True)
    room_amenities = serializers.CharField(source="room.amenities", read_only=True)
    available_slots = serializers.IntegerField(read_only=True)

    class Meta:
        model = ClassSchedule
        fields = (
            "id",
            "gym_class",
            "gym_class_name",
            "trainer",
            "trainer_name",
            "room",
            "room_name",
            "room_amenities",
            "start_time",
            "end_time",
            "max_participants",
            "current_participants",
            "available_slots",
            "status",
            "created_at",
            "updated_at",
        )


class BookingSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    schedule_name = serializers.CharField(source="schedule.gym_class.name", read_only=True)
    start_time = serializers.DateTimeField(source="schedule.start_time", read_only=True)
    end_time = serializers.DateTimeField(source="schedule.end_time", read_only=True)
    trainer_id = serializers.IntegerField(source="schedule.trainer_id", read_only=True)
    trainer_name = serializers.CharField(source="schedule.trainer.name", read_only=True)
    class_price = serializers.DecimalField(source="schedule.gym_class.price", max_digits=10, decimal_places=2, read_only=True)
    gym_class_id = serializers.IntegerField(source="schedule.gym_class_id", read_only=True)
    # VĐ #3: booked_at is now a @property alias for created_at
    booked_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Booking
        fields = (
            "id",
            "user_username",
            "schedule",
            "schedule_name",
            "start_time",
            "end_time",
            "booking_code",
            "status",
            "note",
            "booked_at",
            "cancelled_at",
            "trainer_id",
            "trainer_name",
            "class_price",
            "gym_class_id",
        )
        read_only_fields = (
            "id",
            "user_username",
            "booking_code",
            "status",
            "booked_at",
            "cancelled_at",
            "trainer_id",
            "trainer_name",
            "class_price",
            "gym_class_id",
        )


class TrainerBookingSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    full_name = serializers.CharField(source="user.profile.full_name", read_only=True)
    phone = serializers.CharField(source="user.profile.phone", read_only=True)
    fitness_goals = serializers.CharField(source="user.profile.fitness_goals", read_only=True)
    health_notes = serializers.CharField(source="user.profile.health_notes", read_only=True)
    trainer_name = serializers.CharField(source="trainer.name", read_only=True)
    trainer_session_price = serializers.DecimalField(source="trainer.session_price", max_digits=10, decimal_places=2, read_only=True)
    # VĐ #3: booked_at is now a @property alias for created_at
    booked_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = TrainerBooking
        fields = (
            "id",
            "user_username",
            "full_name",
            "phone",
            "fitness_goals",
            "health_notes",
            "trainer",
            "trainer_name",
            "trainer_session_price",
            "start_time",
            "end_time",
            "booking_code",
            "status",
            "note",
            "booked_at",
            "cancelled_at",
        )
        read_only_fields = (
            "id",
            "user_username",
            "full_name",
            "phone",
            "fitness_goals",
            "health_notes",
            "trainer_name",
            "trainer_session_price",
            "booking_code",
            "status",
            "booked_at",
            "cancelled_at",
        )


class TrainerMonthlyBookingSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    full_name = serializers.CharField(source="user.profile.full_name", read_only=True)
    phone = serializers.CharField(source="user.profile.phone", read_only=True)
    fitness_goals = serializers.CharField(source="user.profile.fitness_goals", read_only=True)
    health_notes = serializers.CharField(source="user.profile.health_notes", read_only=True)
    trainer_name = serializers.CharField(source="trainer.name", read_only=True)
    trainer_session_price = serializers.DecimalField(source="trainer.session_price", max_digits=10, decimal_places=2, read_only=True)
    # VĐ #3: booked_at is now a @property alias for created_at
    booked_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = TrainerMonthlyBooking
        fields = (
            "id",
            "user_username",
            "full_name",
            "phone",
            "fitness_goals",
            "health_notes",
            "trainer",
            "trainer_name",
            "trainer_session_price",
            "start_date",
            "end_date",
            "months",
            "sessions_per_week",
            "preferred_time",
            "booking_code",
            "status",
            "note",
            "booked_at",
            "cancelled_at",
        )
        read_only_fields = (
            "id",
            "user_username",
            "full_name",
            "phone",
            "fitness_goals",
            "health_notes",
            "trainer_name",
            "trainer_session_price",
            "end_date",
            "booking_code",
            "status",
            "booked_at",
            "cancelled_at",
        )


class MembershipPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipPackage
        fields = (
            "id",
            "name",
            "description",
            "price",
            "duration_days",
            "max_bookings_per_week",
            "is_freezable",
            "max_freeze_days",
            "allowed_categories",
            "status",
        )


class UserMembershipSerializer(serializers.ModelSerializer):
    package_name = serializers.CharField(source="package.name", read_only=True)
    package_price = serializers.DecimalField(source="package.price", max_digits=10, decimal_places=2, read_only=True)
    invoice_details = serializers.SerializerMethodField(read_only=True)
    is_freezable = serializers.BooleanField(source="package.is_freezable", read_only=True)
    max_freeze_days = serializers.IntegerField(source="package.max_freeze_days", read_only=True)

    class Meta:
        model = UserMembership
        fields = (
            "id",
            "package",
            "package_name",
            "package_price",
            "start_date",
            "end_date",
            "status",
            "created_at",
            "invoice_details",
            "is_freezable",
            "max_freeze_days",
        )
        read_only_fields = ("id", "package_name", "package_price", "start_date", "end_date", "status", "created_at", "invoice_details", "is_freezable", "max_freeze_days")

    def get_invoice_details(self, obj):
        from gym_booking_backend.infrastructure.models import InvoiceItem
        item = InvoiceItem.objects.filter(item_type="membership", object_id=obj.id).first()
        if item:
            return {
                "id": item.invoice.id,
                "invoice_number": item.invoice.invoice_number,
                "total_amount": item.invoice.total_amount,
                "status": item.invoice.status,
            }
        return None


class PaymentSerializer(serializers.ModelSerializer):
    package_name = serializers.SerializerMethodField(read_only=True)
    payment_title = serializers.SerializerMethodField(read_only=True)
    invoice_id = serializers.IntegerField(source="invoice.id", read_only=True)
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "membership",
            "package_name",
            "payment_title",
            "amount",
            "payment_method",
            "status",
            "paid_at",
            "transaction_code",
            "invoice_id",
            "invoice_number",
            "created_at",
        )
        read_only_fields = (
            "id",
            "package_name",
            "payment_title",
            "amount",
            "status",
            "paid_at",
            "transaction_code",
            "invoice_id",
            "invoice_number",
            "created_at",
        )

    def get_package_name(self, obj):
        if obj.membership_id and obj.membership and obj.membership.package:
            return obj.membership.package.name
        return ""

    def get_payment_title(self, obj):
        if obj.membership_id and obj.membership and obj.membership.package:
            return f"Goi tap: {obj.membership.package.name}"

        if not obj.invoice_id:
            return "Thanh toan khac"

        invoice_item = InvoiceItem.objects.filter(invoice_id=obj.invoice_id).first()
        if not invoice_item:
            return f"Hoa don #{obj.invoice_id}"

        if invoice_item.item_type == "class_fee":
            from gym_booking_backend.infrastructure.models import TrainerBooking

            trainer_booking = TrainerBooking.objects.filter(id=invoice_item.object_id).select_related("trainer").first()
            if trainer_booking:
                return f"Dat lich 1-1: {trainer_booking.trainer.name} ({trainer_booking.booking_code})"
            return "Dat lich 1-1 voi HLV"

        return invoice_item.get_item_type_display()


class ReviewSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    trainer_name = serializers.CharField(source="trainer.name", read_only=True)
    class_name = serializers.CharField(source="gym_class.name", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id",
            "user_username",
            "trainer",
            "trainer_name",
            "gym_class",
            "class_name",
            "rating",
            "comment",
            "created_at",
        )
        read_only_fields = ("id", "user_username", "trainer_name", "class_name", "created_at")


class MembershipFreezeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipFreeze
        # VĐ #11: Khai báo fields cụ thể
        fields = (
            "id", "user_membership", "start_date", "end_date",
            "duration_days", "reason", "created_at", "updated_at",
        )


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = "__all__"


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = "__all__"


class PTPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PTPackage
        fields = "__all__"


class TrainerScheduleSerializer(serializers.ModelSerializer):
    trainer_name = serializers.CharField(source="trainer.name", read_only=True)

    class Meta:
        model = TrainerSchedule
        fields = "__all__"


class PTBookingSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    trainer_name = serializers.CharField(source="trainer.name", read_only=True)

    class Meta:
        model = PTBooking
        fields = "__all__"
        read_only_fields = ("id", "booking_code", "created_at", "updated_at")


class UserPTPackageSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    trainer_name = serializers.CharField(source="trainer.name", read_only=True)
    trainer_email = serializers.EmailField(source="trainer.email", read_only=True)
    package_name = serializers.CharField(source="package.name", read_only=True)
    bookings = PTBookingSerializer(many=True, read_only=True)
    remaining_sessions = serializers.IntegerField(read_only=True)

    class Meta:
        model = UserPTPackage
        fields = (
            "id",
            "user",
            "user_username",
            "trainer",
            "trainer_name",
            "trainer_email",
            "package",
            "package_name",
            "start_date",
            "end_date",
            "total_sessions",
            "used_sessions",
            "remaining_sessions",
            "status",
            "selected_weekdays",
            "start_time",
            "end_time",
            "bookings",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "user_username", "trainer_name", "trainer_email", "package_name", "total_sessions", "used_sessions", "remaining_sessions", "status", "bookings", "created_at", "updated_at")


class MonthlyPTBookingCreateSerializer(serializers.Serializer):
    package = serializers.IntegerField()
    trainer = serializers.IntegerField()
    start_date = serializers.DateField()
    weekdays = serializers.ListField(child=serializers.IntegerField(min_value=0, max_value=6))
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_start_date(self, value):
        from django.utils import timezone
        if value < timezone.localdate():
            raise serializers.ValidationError("Ngày bắt đầu không được nhỏ hơn ngày hôm nay.")
        return value

    def validate(self, data):
        if data["start_time"] >= data["end_time"]:
            raise serializers.ValidationError("Giờ bắt đầu phải trước giờ kết thúc.")
        return data

