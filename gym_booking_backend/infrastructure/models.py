from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from gym_booking_backend.domain.constants import (
    BookingStatus,
    CommonStatus,
    DifficultyLevel,
    GenderChoices,
    MembershipStatus,
    PaymentMethod,
    PaymentStatus,
    RoomStatus,
    ScheduleStatus,
    UserRole,
    InvoiceStatus,
    InvoiceItemType,
    RatingChoices,
    UserPTPackageStatus,
    PTBookingStatus,
    WeekdayChoices,
)


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True



class Profile(TimestampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=20, choices=GenderChoices.choices, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.MEMBER)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    health_notes = models.TextField(blank=True)
    fitness_goals = models.TextField(blank=True)

    class Meta:
        ordering = ["full_name", "id"]

    def __str__(self):
        return self.full_name or self.user.username


class Trainer(TimestampedModel):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="trainer_profile")
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    specialty = models.CharField(max_length=100)
    experience_years = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True)
    certifications = models.TextField(blank=True)
    session_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to="trainers/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=CommonStatus.choices, default=CommonStatus.ACTIVE)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class Room(TimestampedModel):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField()
    amenities = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=RoomStatus.choices, default=RoomStatus.ACTIVE)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class Category(TimestampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=CommonStatus.choices, default=CommonStatus.ACTIVE)

    class Meta:
        ordering = ["name", "id"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class GymClass(TimestampedModel):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="classes")
    trainer = models.ForeignKey(Trainer, on_delete=models.PROTECT, related_name="classes")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    difficulty_level = models.CharField(
        max_length=20,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.BEGINNER,
    )
    duration_minutes = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to="classes/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=CommonStatus.choices, default=CommonStatus.ACTIVE)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class ClassSchedule(TimestampedModel):
    gym_class = models.ForeignKey(GymClass, on_delete=models.CASCADE, related_name="schedules")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="schedules")
    trainer = models.ForeignKey(Trainer, on_delete=models.PROTECT, related_name="schedules", null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    max_participants = models.PositiveIntegerField()
    current_participants = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=ScheduleStatus.choices, default=ScheduleStatus.OPEN)

    class Meta:
        ordering = ["start_time", "id"]

    def __str__(self):
        return f"{self.gym_class.name} - {self.start_time:%Y-%m-%d %H:%M}"

    def clean(self):
        from django.core.exceptions import ValidationError
        from gym_booking_backend.infrastructure.repositories import schedule_repository
        
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("Start time must be before end time.")
            
            # Check room conflict
            if schedule_repository.has_room_conflict(self.room, self.start_time, self.end_time, self.id):
                raise ValidationError(f"Room {self.room.name} is already booked during this time range.")
            
            # Check trainer conflict
            trainer = self.trainer or (self.gym_class.trainer if self.gym_class_id else None)
            if trainer and schedule_repository.has_trainer_conflict(trainer, self.start_time, self.end_time, self.id):
                raise ValidationError(f"Trainer {trainer.name} is already scheduled during this time range.")

    def save(self, *args, **kwargs):
        if not self.trainer_id and self.gym_class_id:
            self.trainer = self.gym_class.trainer
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def available_slots(self):
        return max(self.max_participants - self.current_participants, 0)


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE, related_name="bookings")
    booking_code = models.CharField(max_length=30, unique=True)
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    note = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    booked_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-booked_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "schedule"],
                condition=models.Q(status__in=["pending", "confirmed"]),
                name="unique_active_booking",
            )
        ]

    def __str__(self):
        return self.booking_code


class TrainerBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trainer_bookings")
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name="personal_bookings")
    booking_code = models.CharField(max_length=30, unique=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    note = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    booked_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-booked_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "trainer", "start_time"],
                condition=models.Q(status__in=["pending", "confirmed"]),
                name="unique_active_trainer_booking",
            )
        ]

    def __str__(self):
        return self.booking_code


class TrainerMonthlyBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trainer_monthly_bookings")
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name="monthly_bookings")
    booking_code = models.CharField(max_length=30, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    months = models.PositiveIntegerField(default=1)
    sessions_per_week = models.PositiveIntegerField(default=3)
    preferred_time = models.TimeField(null=True, blank=True)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    cancellation_reason = models.TextField(blank=True)
    booked_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-booked_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "trainer", "start_date"],
                condition=models.Q(status__in=["pending", "confirmed"]),
                name="unique_active_trainer_monthly_booking",
            )
        ]

    def __str__(self):
        return self.booking_code


class MembershipPackage(TimestampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    max_bookings_per_week = models.PositiveIntegerField(null=True, blank=True)
    is_freezable = models.BooleanField(default=True)
    max_freeze_days = models.PositiveIntegerField(default=30)
    allowed_categories = models.ManyToManyField(Category, blank=True, related_name="membership_packages")
    status = models.CharField(max_length=20, choices=CommonStatus.choices, default=CommonStatus.ACTIVE)

    class Meta:
        ordering = ["price", "name"]

    def __str__(self):
        return self.name


class UserMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    package = models.ForeignKey(MembershipPackage, on_delete=models.PROTECT, related_name="user_memberships")
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=MembershipStatus.choices, default=MembershipStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "id"]

    def __str__(self):
        return f"{self.user.username} - {self.package.name}"


class MembershipFreeze(TimestampedModel):
    user_membership = models.ForeignKey(UserMembership, on_delete=models.CASCADE, related_name="freezes")
    start_date = models.DateField()
    end_date = models.DateField()
    duration_days = models.PositiveIntegerField()
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Freeze for {self.user_membership.user.username} ({self.duration_days} days)"



class Invoice(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invoices")
    invoice_number = models.CharField(max_length=50, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.UNPAID)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.invoice_number



class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    item_type = models.CharField(max_length=20, choices=InvoiceItemType.choices)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.item_type} - {self.amount}"


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    membership = models.ForeignKey(UserMembership, on_delete=models.CASCADE, related_name="payments", null=True, blank=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    transaction_code = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_gateway_response = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "id"]

    def __str__(self):
        return self.transaction_code or f"Payment #{self.pk}"


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name="reviews", null=True, blank=True)
    gym_class = models.ForeignKey(GymClass, on_delete=models.CASCADE, related_name="reviews", null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviews")
    rating = models.PositiveSmallIntegerField(choices=RatingChoices.choices, validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "id"]

    def __str__(self):
        target = self.trainer or self.gym_class
        return f"{self.user.username} - {target} ({self.rating})"


class PTPackage(TimestampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(help_text="Thời hạn gói (ngày)")
    total_sessions = models.PositiveIntegerField(help_text="Tổng số buổi tập")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["price", "name"]

    def __str__(self):
        return f"{self.name} ({self.total_sessions} sessions / {self.duration_days} days)"


class TrainerSchedule(TimestampedModel):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name="pt_schedules")
    weekday = models.IntegerField(choices=WeekdayChoices.choices, help_text="Thứ trong tuần (0=Monday)")
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["trainer", "weekday", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["trainer", "weekday", "start_time"],
                name="unique_trainer_weekday_start_time"
            )
        ]

    def __str__(self):
        return f"{self.trainer.name} - Weekday {self.get_weekday_display()} ({self.start_time} - {self.end_time})"


class UserPTPackage(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_pt_packages")
    trainer = models.ForeignKey(Trainer, on_delete=models.PROTECT, related_name="member_pt_packages")
    package = models.ForeignKey(PTPackage, on_delete=models.PROTECT, related_name="purchases")
    start_date = models.DateField()
    end_date = models.DateField()
    total_sessions = models.PositiveIntegerField()
    used_sessions = models.PositiveIntegerField(default=0)
    remaining_sessions = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=UserPTPackageStatus.choices,
        default=UserPTPackageStatus.ACTIVE,
    )
    selected_weekdays = models.CharField(
        max_length=50,
        help_text="Danh sách thứ tự chọn (ví dụ: '0,2,4')",
    )
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.package.name} with {self.trainer.name}"


class PTBooking(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pt_bookings")
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name="pt_trainer_bookings")
    user_pt_package = models.ForeignKey(UserPTPackage, on_delete=models.CASCADE, related_name="bookings")
    booking_code = models.CharField(max_length=30, unique=True)
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=PTBookingStatus.choices,
        default=PTBookingStatus.CONFIRMED,
    )
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["booking_date", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["trainer", "booking_date", "start_time"],
                condition=models.Q(status__in=["confirmed", "pending"]),
                name="unique_trainer_pt_booking_slot"
            ),
            models.UniqueConstraint(
                fields=["user", "booking_date", "start_time"],
                condition=models.Q(status__in=["confirmed", "pending"]),
                name="unique_user_pt_booking_slot"
            )
        ]

    def __str__(self):
        return f"{self.booking_code} - {self.booking_date} ({self.start_time}-{self.end_time})"
