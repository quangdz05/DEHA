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
    UserMembership,
)


class Command(BaseCommand):
    help = "Create demo data for the gym booking backend."

    @transaction.atomic
    def handle(self, *args, **options):
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

        categories = self._create_categories()
        trainers = self._create_trainers()
        rooms = self._create_rooms()
        classes = self._create_classes(categories, trainers)
        schedules = self._create_schedules(classes, rooms)
        packages = self._create_membership_packages()
        memberships = self._create_memberships([member_1, member_2], packages)
        self._create_payments(memberships)
        self._create_bookings(member_1, schedules)
        self._create_reviews(member_1, member_2, trainers, classes)
        self._sync_schedule_participants()

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

    def _create_categories(self):
        data = [
            ("Yoga", "Cac lop yoga giup tang do deo dai va can bang co the."),
            ("Cardio", "Bai tap tang suc ben va dot mo."),
            ("Boxing", "Lop boxing nang cao phan xa va the luc."),
            ("Zumba", "Lop nhay ket hop cardio vui nhon."),
            ("Weight Training", "Luyen tap suc manh voi ta va may tap."),
        ]
        return {
            name: Category.objects.update_or_create(
                name=name,
                defaults={"description": description, "status": CommonStatus.ACTIVE},
            )[0]
            for name, description in data
        }

    def _create_trainers(self):
        data = [
            ("Nguyen Van A", "vana@gym.local", "0901111111", "Yoga", 6, "HLV yoga va stretching."),
            ("Tran Thi B", "thib@gym.local", "0902222222", "Cardio", 5, "HLV cardio va giam mo."),
            ("Le Van C", "vanc@gym.local", "0903333333", "Boxing", 8, "HLV boxing co kinh nghiem thi dau."),
            ("Pham Thi D", "thid@gym.local", "0904444444", "Zumba", 4, "HLV zumba va dance fitness."),
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

    def _create_classes(self, categories, trainers):
        data = [
            ("Yoga co ban", "Yoga", "Yoga", DifficultyLevel.BEGINNER, 60, "Yoga cho nguoi moi bat dau."),
            ("Yoga nang cao", "Yoga", "Yoga", DifficultyLevel.ADVANCED, 75, "Yoga nang cao suc ben va kha nang giu thang bang."),
            ("Cardio dot mo", "Cardio", "Cardio", DifficultyLevel.INTERMEDIATE, 45, "Cardio cuong do vua."),
            ("Boxing co ban", "Boxing", "Boxing", DifficultyLevel.BEGINNER, 60, "Ky thuat boxing nen tang."),
            ("Zumba nang dong", "Zumba", "Zumba", DifficultyLevel.BEGINNER, 50, "Zumba vui nhon cho moi trinh do."),
            (
                "Weight Training",
                "Weight Training",
                "Personal Trainer",
                DifficultyLevel.INTERMEDIATE,
                60,
                "Tap suc manh voi ta va may tap.",
            ),
        ]
        classes = {}
        for name, category, specialty, level, duration, description in data:
            gym_class, _ = GymClass.objects.update_or_create(
                name=name,
                defaults={
                    "category": categories[category],
                    "trainer": trainers[specialty],
                    "difficulty_level": level,
                    "duration_minutes": duration,
                    "description": description,
                    "status": CommonStatus.ACTIVE,
                },
            )
            classes[name] = gym_class
        return classes

    def _create_schedules(self, classes, rooms):
        today = timezone.localdate()
        schedule_data = [
            ("Yoga co ban", "Room A", 1, time(18, 0), 20),
            ("Cardio dot mo", "Room B", 1, time(19, 30), 15),
            ("Boxing co ban", "Room C", 2, time(18, 30), 20),
            ("Zumba nang dong", "Room A", 3, time(17, 30), 20),
            ("Weight Training", "Room C", 4, time(19, 0), 25),
            ("Yoga nang cao", "Room B", 5, time(18, 0), 15),
            ("Cardio dot mo", "Room A", 6, time(7, 0), 20),
        ]
        schedules = []
        for class_name, room_name, day_offset, start_at, max_participants in schedule_data:
            gym_class = classes[class_name]
            start_date = today + timedelta(days=day_offset)
            start_time = timezone.make_aware(datetime.combine(start_date, start_at), timezone.get_current_timezone())
            end_time = start_time + timedelta(minutes=gym_class.duration_minutes)
            schedule, _ = ClassSchedule.objects.update_or_create(
                gym_class=gym_class,
                room=rooms[room_name],
                start_time=start_time,
                defaults={
                    "end_time": end_time,
                    "max_participants": max_participants,
                    "status": ScheduleStatus.OPEN,
                },
            )
            schedules.append(schedule)
        return schedules

    def _create_membership_packages(self):
        data = [
            ("Basic", "Goi co ban 3 buoi moi tuan.", Decimal("300000.00"), 30, 3),
            ("Premium", "Goi nang cao 5 buoi moi tuan.", Decimal("500000.00"), 30, 5),
            ("VIP", "Goi VIP khong gioi han so buoi.", Decimal("800000.00"), 30, None),
        ]
        return {
            name: MembershipPackage.objects.update_or_create(
                name=name,
                defaults={
                    "description": description,
                    "price": price,
                    "duration_days": duration_days,
                    "max_bookings_per_week": max_per_week,
                    "status": CommonStatus.ACTIVE,
                },
            )[0]
            for name, description, price, duration_days, max_per_week in data
        }

    def _create_memberships(self, users, packages):
        today = timezone.localdate()
        data = [(users[0], packages["Basic"]), (users[1], packages["Premium"])]
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

    def _create_bookings(self, user, schedules):
        for index, schedule in enumerate(schedules[:2], start=1):
            Booking.objects.update_or_create(
                booking_code=f"SEED-BK-{user.username.upper()}-{index}",
                defaults={
                    "user": user,
                    "schedule": schedule,
                    "status": BookingStatus.CONFIRMED,
                    "note": "Du lieu mau",
                },
            )

    def _create_reviews(self, member_1, member_2, trainers, classes):
        Review.objects.update_or_create(
            user=member_1,
            trainer=trainers["Yoga"],
            defaults={"rating": 5, "comment": "HLV huong dan rat de hieu.", "gym_class": None},
        )
        Review.objects.update_or_create(
            user=member_2,
            gym_class=classes["Cardio dot mo"],
            defaults={"rating": 4, "comment": "Lop tap soi dong va hieu qua.", "trainer": None},
        )

    def _sync_schedule_participants(self):
        for schedule in ClassSchedule.objects.all():
            count = schedule.bookings.filter(status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]).count()
            status = ScheduleStatus.FULL if count >= schedule.max_participants else ScheduleStatus.OPEN
            ClassSchedule.objects.filter(id=schedule.id).update(current_participants=count, status=status)
