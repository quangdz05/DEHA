from django.db import models


class GenderChoices(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"


class CommonStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class RoomStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    MAINTENANCE = "maintenance", "Maintenance"
    INACTIVE = "inactive", "Inactive"


class DifficultyLevel(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    ADVANCED = "advanced", "Advanced"


class ScheduleStatus(models.TextChoices):
    OPEN = "open", "Open"
    FULL = "full", "Full"
    CANCELLED = "cancelled", "Cancelled"
    COMPLETED = "completed", "Completed"


class BookingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"
    COMPLETED = "completed", "Completed"
    NO_SHOW = "no_show", "No show"
    WAITLIST = "waitlist", "Waitlist"



class MembershipStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Cash"
    BANK_TRANSFER = "bank_transfer", "Bank transfer"
    MOMO = "momo", "MoMo"
    VNPAY = "vnpay", "VNPay"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"


class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    TRAINER = "trainer", "Trainer"
    MEMBER = "member", "Member"


class InvoiceStatus(models.TextChoices):
    UNPAID = "unpaid", "Unpaid"
    PAID = "paid", "Paid"
    CANCELLED = "cancelled", "Cancelled"


class InvoiceItemType(models.TextChoices):
    MEMBERSHIP = "membership", "Membership"
    CLASS_FEE = "class_fee", "Class Fee"
    MERCHANDISE = "merchandise", "Merchandise"
    PENALTY = "penalty", "Penalty"


class RatingChoices(models.IntegerChoices):
    ONE = 1, "1 Star"
    TWO = 2, "2 Stars"
    THREE = 3, "3 Stars"
    FOUR = 4, "4 Stars"
    FIVE = 5, "5 Stars"


class UserPTPackageStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class PTBookingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class WeekdayChoices(models.IntegerChoices):
    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"


