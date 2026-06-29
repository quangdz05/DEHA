from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from gym_booking_backend.domain.constants import (
    BookingStatus,
    CommonStatus,
    DifficultyLevel,
    GenderChoices,
    MembershipStatus,
    PaymentMethod,
    PaymentStatus,
    ScheduleStatus,
)
from gym_booking_backend.infrastructure.models import (
    MembershipPackage,
    Payment,
    Profile,
    Review,
    Room,
    Trainer,
    UserMembership,
    TrainerSchedule,
)


class Command(BaseCommand):
    help = "Create demo data for the gym booking backend."

    @transaction.atomic
    def handle(self, *args, **options):
        # Clean up database tables to avoid conflicts
        from gym_booking_backend.infrastructure.models import (
            UserMembership, Payment, Review, TrainerSchedule, PTBooking, UserPTPackage, Invoice, InvoiceItem
        )
        Payment.objects.all().delete()
        InvoiceItem.objects.all().delete()
        Invoice.objects.all().delete()
        UserMembership.objects.all().delete()
        Review.objects.all().delete()
        PTBooking.objects.all().delete()
        UserPTPackage.objects.all().delete()
        TrainerSchedule.objects.all().delete()

        admin = self._create_user(
            username="admin",
            password="admin123456",
            email="admin@gym.local",
            first_name="Gym",
            last_name="Admin",
            is_staff=True,
            is_superuser=True,
        )
        member_1 = self._create_user(
            username="member1",
            password="12345678",
            email="member1@gym.local",
            first_name="Minh",
            last_name="Nguyen",
        )
        member_2 = self._create_user(
            username="member2",
            password="12345678",
            email="member2@gym.local",
            first_name="Lan",
            last_name="Tran",
        )

        self._create_profile(admin, "Gym Admin", "0900000000", GenderChoices.OTHER, "Quan ly he thong")
        self._create_profile(member_1, "Nguyen Van Minh", "0912345678", GenderChoices.MALE, "Quan 1, TP.HCM")
        self._create_profile(member_2, "Tran Thi Lan", "0987654321", GenderChoices.FEMALE, "Quan 3, TP.HCM")

        trainers = self._create_trainers()
        rooms = self._create_rooms()
        packages = self._create_membership_packages()
        memberships = self._create_memberships([member_1, member_2], packages)
        self._create_payments(memberships)
        self._create_reviews(member_1, member_2, trainers)
        self._create_trainer_schedules(trainers)

        self.stdout.write(self.style.SUCCESS("Seed data created successfully."))
        self.stdout.write("Admin: username=admin password=admin123456")
        self.stdout.write("Demo users: member1/12345678, member2/12345678")

    def _create_user(self, username, password, email, first_name, last_name, is_staff=False, is_superuser=False):
        user, _ = User.objects.update_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
                "is_active": True,
            },
        )
        user.set_password(password)
        user.save()
        return user

    def _create_profile(self, user, full_name, phone, gender, address):
        Profile.objects.update_or_create(
            user=user,
            defaults={
                "full_name": full_name,
                "phone": phone,
                "gender": gender,
                "address": address,
            },
        )



    def _create_trainers(self):
        data = [
            ("Nguyen Van A", "vana@gym.local", "0901111111", "Yoga", 6, "HLV yoga va stretching."),
            ("Tran Thi B", "thib@gym.local", "0902222222", "Cardio", 5, "HLV cardio va giam mo."),
            ("Hoang Van E", "vane@gym.local", "0905555555", "Personal Trainer", 10, "HLV ca nhan va strength training."),
        ]
        trainers = {}
        for name, email, phone, specialty, years, bio in data:
            trainer, _ = Trainer.objects.update_or_create(
                email=email,
                defaults={
                    "name": name,
                    "phone": phone,
                    "specialty": specialty,
                    "experience_years": years,
                    "bio": bio,
                    "status": CommonStatus.ACTIVE,
                },
            )
            trainers[specialty] = trainer
        return trainers

    def _create_rooms(self):
        data = [
            ("Room A", "Tang 1", 20),
            ("Room B", "Tang 2", 15),
            ("Room C", "Tang 3", 25),
        ]
        return {
            name: Room.objects.update_or_create(
                name=name,
                defaults={"location": location, "capacity": capacity, "status": "active"},
            )[0]
            for name, location, capacity in data
        }



    def _create_membership_packages(self):
        from gym_booking_backend.infrastructure.models import UserMembership
        data = [
            ("Gói 1 tháng", "Thẻ hội viên tập luyện trong 1 tháng.", Decimal("300000.00"), 30, None),
            ("Gói 3 tháng", "Thẻ hội viên tập luyện trong 3 tháng.", Decimal("800000.00"), 90, None),
            ("Gói 6 tháng", "Thẻ hội viên tập luyện trong 6 tháng.", Decimal("1500000.00"), 180, None),
            ("Gói 12 tháng", "Thẻ hội viên tập luyện trong 12 tháng.", Decimal("2800000.00"), 360, None),
        ]
        
        new_packages = {}
        for name, description, price, duration_days, max_per_week in data:
            pkg, _ = MembershipPackage.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "price": price,
                    "duration_days": duration_days,
                    "max_bookings_per_week": max_per_week,
                    "status": CommonStatus.ACTIVE,
                },
            )
            new_packages[name] = pkg

        # Migrate user memberships and delete old packages
        basic_pkg = MembershipPackage.objects.filter(name="Basic").first()
        premium_pkg = MembershipPackage.objects.filter(name="Premium").first()
        vip_pkg = MembershipPackage.objects.filter(name="VIP").first()
        
        if basic_pkg:
            UserMembership.objects.filter(package=basic_pkg).update(package=new_packages["Gói 1 tháng"])
            basic_pkg.delete()
        if premium_pkg:
            UserMembership.objects.filter(package=premium_pkg).update(package=new_packages["Gói 3 tháng"])
            premium_pkg.delete()
        if vip_pkg:
            UserMembership.objects.filter(package=vip_pkg).update(package=new_packages["Gói 12 tháng"])
            vip_pkg.delete()

        return new_packages

    def _create_memberships(self, users, packages):
        today = timezone.localdate()
        data = [(users[0], packages["Gói 1 tháng"]), (users[1], packages["Gói 3 tháng"])]
        memberships = []
        for user, package in data:
            membership, _ = UserMembership.objects.update_or_create(
                user=user,
                package=package,
                status=MembershipStatus.ACTIVE,
                defaults={
                    "start_date": today,
                    "end_date": today + timedelta(days=package.duration_days),
                },
            )
            memberships.append(membership)
        return memberships

    def _create_payments(self, memberships):
        for membership in memberships:
            Payment.objects.update_or_create(
                transaction_code=f"SEED-{membership.user.username.upper()}-{membership.package.name.upper()}",
                defaults={
                    "user": membership.user,
                    "membership": membership,
                    "amount": membership.package.price,
                    "payment_method": PaymentMethod.CASH,
                    "status": PaymentStatus.SUCCESS,
                    "paid_at": timezone.now(),
                },
            )

    def _create_reviews(self, member_1, member_2, trainers):
        Review.objects.update_or_create(
            user=member_1,
            trainer=trainers["Yoga"],
            defaults={"rating": 5, "comment": "HLV huong dan rat de hieu."},
        )
        Review.objects.update_or_create(
            user=member_2,
            trainer=trainers["Cardio"],
            defaults={"rating": 4, "comment": "Lop tap soi dong va hieu qua."},
        )

    # _create_pt_packages removed

    def _create_trainer_schedules(self, trainers):
        for specialty, trainer in trainers.items():
            for weekday in [0, 1, 2, 3, 4]: # Mon-Fri
                TrainerSchedule.objects.update_or_create(
                    trainer=trainer,
                    weekday=weekday,
                    start_time=time(8, 0),
                    defaults={
                        "end_time": time(20, 0),
                        "is_available": True,
                    }
                )
