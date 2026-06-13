from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from gym_booking_backend.infrastructure.models import (
    Profile,
    Trainer,
    Category,
    Room,
    GymClass,
    ClassSchedule,
    Booking,
    MembershipPackage,
    UserMembership,
    Payment,
)
from gym_booking_backend.domain.constants import BookingStatus, PaymentStatus, MembershipStatus, UserRole
from django.utils import timezone
from datetime import timedelta

class RoleAuthAndDashboardTests(APITestCase):
    def setUp(self):
        # Create standard Member
        self.member_user = User.objects.create_user(
            username="member_test",
            password="testpassword",
            email="member@test.com",
            first_name="Member",
            last_name="Test"
        )
        self.member_profile = Profile.objects.create(
            user=self.member_user,
            full_name="Member Test",
            role=UserRole.MEMBER
        )

        # Create Trainer
        self.trainer_user = User.objects.create_user(
            username="trainer_test",
            password="testpassword",
            email="trainer@test.com",
            first_name="Trainer",
            last_name="Test"
        )
        self.trainer_profile = Profile.objects.create(
            user=self.trainer_user,
            full_name="Trainer Test",
            role=UserRole.TRAINER
        )
        self.trainer_record = Trainer.objects.create(
            user=self.trainer_user,
            name="Trainer Test",
            email="trainer@test.com",
            phone="123456789",
            specialty="Pilates",
            experience_years=3
        )

        # Create Admin
        self.admin_user = User.objects.create_user(
            username="admin_test",
            password="testpassword",
            email="admin@test.com",
            first_name="Admin",
            last_name="Test"
        )
        self.admin_profile = Profile.objects.create(
            user=self.admin_user,
            full_name="Admin Test",
            role=UserRole.ADMIN
        )

        # Create other trainer to verify schedule filtering
        self.other_trainer_user = User.objects.create_user(
            username="other_trainer",
            password="testpassword",
            email="other@test.com"
        )
        self.other_trainer_profile = Profile.objects.create(
            user=self.other_trainer_user,
            full_name="Other Trainer",
            role=UserRole.TRAINER
        )
        self.other_trainer_record = Trainer.objects.create(
            user=self.other_trainer_user,
            name="Other Trainer",
            email="other@test.com",
            phone="987654321"
        )

        # Setup standard domain entities
        self.category = Category.objects.create(name="Fitness")
        self.room = Room.objects.create(name="Studio A", location="Level 1", capacity=10)
        self.gym_class = GymClass.objects.create(
            category=self.category,
            trainer=self.trainer_record,
            name="Core Strength",
            duration_minutes=45
        )
        self.other_gym_class = GymClass.objects.create(
            category=self.category,
            trainer=self.other_trainer_record,
            name="Spin Class",
            duration_minutes=45
        )

        # Class Schedules
        self.schedule = ClassSchedule.objects.create(
            gym_class=self.gym_class,
            room=self.room,
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=1),
            max_participants=10,
            current_participants=1
        )
        self.other_schedule = ClassSchedule.objects.create(
            gym_class=self.other_gym_class,
            room=self.room,
            start_time=timezone.now() + timedelta(days=2),
            end_time=timezone.now() + timedelta(days=2, hours=1),
            max_participants=5,
            current_participants=0
        )

        # Booking
        self.booking = Booking.objects.create(
            user=self.member_user,
            schedule=self.schedule,
            booking_code="BKT-TEST-001",
            status=BookingStatus.PENDING,
            note="Test booking note"
        )

        # Membership Package & Membership & Payment
        self.package = MembershipPackage.objects.create(
            name="Vip Monthly",
            price=100000.00,
            duration_days=30
        )
        self.membership = UserMembership.objects.create(
            user=self.member_user,
            package=self.package,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date(),
            status=MembershipStatus.ACTIVE
        )
        self.payment = Payment.objects.create(
            user=self.member_user,
            membership=self.membership,
            amount=100000.00,
            payment_method="bank_transfer",
            status=PaymentStatus.PENDING,
            transaction_code="TXN_TEST_001"
        )

    def test_register_role_handling(self):
        # Register a member
        register_url = reverse("auth-register")
        data = {
            "username": "new_member_user",
            "email": "new_member@test.com",
            "password": "Newpassword123!",
            "first_name": "New",
            "last_name": "Member",
            "role": "member"
        }
        response = self.client.post(register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], "member")
        
        # Register a trainer and check Trainer entity creation
        data_trainer = {
            "username": "new_trainer_user",
            "email": "new_trainer@test.com",
            "password": "Newpassword123!",
            "first_name": "New",
            "last_name": "Trainer",
            "role": "trainer"
        }
        response = self.client.post(register_url, data_trainer, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], "trainer")
        self.assertTrue(Trainer.objects.filter(user__username="new_trainer_user").exists())

    def test_login_promotes_staff_superuser_to_admin(self):
        superuser = User.objects.create_superuser(
            username="super_test",
            password="superpassword",
            email="super@test.com"
        )
        # Login
        login_url = reverse("auth-login")
        response = self.client.post(login_url, {"username": "super_test", "password": "superpassword"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "admin")
        self.assertTrue(Profile.objects.filter(user=superuser, role="admin").exists())

    def test_admin_dashboard_permissions(self):
        # Try accessing admin bookings as member (should be forbidden)
        self.client.force_authenticate(user=self.member_user)
        url = reverse("admin-bookings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try accessing as trainer (should be forbidden)
        self.client.force_authenticate(user=self.trainer_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Access as admin (should be successful)
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["booking_code"], "BKT-TEST-001")

    def test_admin_booking_status_update(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("admin-booking-status", args=[self.booking.id])
        
        # Confirm booking
        response = self.client.post(url, {"status": BookingStatus.CONFIRMED}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CONFIRMED)
        
        # Cancel booking and verify schedule current_participants decreases
        initial_participants = self.schedule.current_participants
        response = self.client.post(url, {"status": BookingStatus.CANCELLED}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.schedule.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CANCELLED)
        self.assertEqual(self.schedule.current_participants, initial_participants - 1)

    def test_admin_payments_and_confirm(self):
        self.client.force_authenticate(user=self.admin_user)
        payments_url = reverse("admin-payments")
        
        response = self.client.get(payments_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        confirm_url = reverse("admin-payment-confirm", args=[self.payment.id])
        response = self.client.post(confirm_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.membership.refresh_from_db()
        self.assertEqual(self.payment.status, PaymentStatus.SUCCESS)
        self.assertEqual(self.membership.status, MembershipStatus.ACTIVE)

    def test_trainer_dashboard_schedules_and_roster(self):
        # Access trainer schedules as member (should be forbidden)
        self.client.force_authenticate(user=self.member_user)
        schedules_url = reverse("trainer-schedules")
        response = self.client.get(schedules_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Access as trainer (should succeed)
        self.client.force_authenticate(user=self.trainer_user)
        response = self.client.get(schedules_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return trainer's schedule, not the other trainer's
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.schedule.id)

        # Get participant list for my schedule (should succeed)
        roster_url = reverse("trainer-schedule-bookings", args=[self.schedule.id])
        response = self.client.get(roster_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["username"], "member_test")

        # Get participant list for other trainer's schedule (should return 404/forbidden)
        other_roster_url = reverse("trainer-schedule-bookings", args=[self.other_schedule.id])
        response = self.client.get(other_roster_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_schedule_auto_populates_trainer(self):
        # Create a new schedule without trainer
        new_schedule = ClassSchedule.objects.create(
            gym_class=self.gym_class,
            room=self.room,
            start_time=timezone.now() + timedelta(days=3),
            end_time=timezone.now() + timedelta(days=3, hours=1),
            max_participants=10
        )
        # Verify trainer is auto-populated from gym_class.trainer
        self.assertEqual(new_schedule.trainer, self.gym_class.trainer)

    def test_unique_active_booking_constraint(self):
        from django.db import IntegrityError, transaction
        # Try to create a duplicate active booking for the same user and schedule
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Booking.objects.create(
                    user=self.member_user,
                    schedule=self.schedule,
                    booking_code="BKT-TEST-DUPLICATE",
                    status=BookingStatus.PENDING
                )

        # However, if the booking is CANCELLED, we should be able to create a new active booking
        self.booking.status = BookingStatus.CANCELLED
        self.booking.save()
        
        # This should succeed because the previous one is CANCELLED
        new_booking = Booking.objects.create(
            user=self.member_user,
            schedule=self.schedule,
            booking_code="BKT-TEST-NEW",
            status=BookingStatus.PENDING
        )
        self.assertEqual(new_booking.booking_code, "BKT-TEST-NEW")

    def test_membership_package_category_restriction(self):
        # Create a category that is NOT allowed for the package
        other_category = Category.objects.create(name="Advanced Yoga")
        package_with_restriction = MembershipPackage.objects.create(
            name="Yoga Only Package",
            price=50000.00,
            duration_days=30
        )
        # Only allow the original category
        package_with_restriction.allowed_categories.add(self.category)
        
        restricted_gym_class = GymClass.objects.create(
            category=other_category,
            trainer=self.trainer_record,
            name="Restricted Advanced Yoga Class",
            duration_minutes=60
        )
        restricted_schedule = ClassSchedule.objects.create(
            gym_class=restricted_gym_class,
            room=self.room,
            start_time=timezone.now() + timedelta(days=5),
            end_time=timezone.now() + timedelta(days=5, hours=1),
            max_participants=10
        )
        
        # Change member membership to the restricted package
        self.membership.package = package_with_restriction
        self.membership.save()
        
        # Try to book the restricted class - should raise an exception in create_booking
        from gym_booking_backend.domain.exceptions import MembershipRequiredException
        from gym_booking_backend.application.services import booking_service
        
        with self.assertRaises(MembershipRequiredException):
            booking_service.create_booking(self.member_user, restricted_schedule.id)

    def test_trainer_attendance_marking(self):
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse("trainer-booking-attendance", args=[self.booking.id])
        
        # Mark as completed
        response = self.client.post(url, {"status": "completed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, "completed")
        
        # Mark as no_show
        response = self.client.post(url, {"status": "no_show"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, "no_show")

        # Unauthorized access to other trainer's schedule booking
        # Create a booking on self.other_schedule
        other_booking = Booking.objects.create(
            user=self.member_user,
            schedule=self.other_schedule,
            booking_code="BKT-TEST-OTHER-01",
            status=BookingStatus.PENDING
        )
        url_other = reverse("trainer-booking-attendance", args=[other_booking.id])
        response = self.client.post(url_other, {"status": "completed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_membership_freezing(self):
        self.client.force_authenticate(user=self.member_user)
        url = reverse("membership-freeze", args=[self.membership.id])
        
        start_date = (timezone.now() + timedelta(days=2)).date()
        end_date = (timezone.now() + timedelta(days=7)).date() # 5 days duration
        
        initial_end_date = self.membership.end_date
        response = self.client.post(url, {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "reason": "Vocation vacation"
        }, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.end_date, initial_end_date + timedelta(days=5))

    def test_admin_schedule_creation_with_overlap_checks(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("admin-schedule-create")
        
        # Try to create a schedule that overlaps in room Studio A
        overlap_start = self.schedule.start_time + timedelta(minutes=15)
        overlap_end = overlap_start + timedelta(hours=1)
        
        data = {
            "gym_class": self.gym_class.id,
            "room": self.room.id,
            "start_time": overlap_start.isoformat(),
            "end_time": overlap_end.isoformat(),
            "max_participants": 15
        }
        
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)
        
        # Create a valid schedule with no overlap
        valid_start = self.schedule.start_time + timedelta(hours=3)
        valid_end = valid_start + timedelta(hours=1)
        
        valid_data = {
            "gym_class": self.gym_class.id,
            "room": self.room.id,
            "start_time": valid_start.isoformat(),
            "end_time": valid_end.isoformat(),
            "max_participants": 15
        }
        response = self.client.post(url, valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_immediate_payment_and_membership_flow(self):
        # 1. Create a member with no membership
        test_user = User.objects.create_user(
            username="test_immediate_pay_user",
            password="password123",
            email="test_pay@test.com"
        )
        Profile.objects.create(
            user=test_user,
            full_name="Test Immediate Pay User",
            role=UserRole.MEMBER
        )
        
        # Authenticate
        self.client.force_authenticate(user=test_user)
        
        # Try to book a class before having any membership - should fail
        booking_url = reverse("booking-create")
        booking_data = {
            "schedule": self.schedule.id,
            "note": "Want to join"
        }
        response = self.client.post(booking_url, booking_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 2. Register a package
        reg_url = reverse("membership-create")
        reg_data = {"package": self.package.id}
        response = self.client.post(reg_url, reg_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        membership_id = response.data["id"]
        # Verify status is PENDING
        self.assertEqual(response.data["status"], MembershipStatus.PENDING)
        
        # Try to book a class with a PENDING membership - should fail
        response = self.client.post(booking_url, booking_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Try to register another package while one is PENDING - should fail
        response = self.client.post(reg_url, reg_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 3. Create and confirm payment
        pay_url = reverse("payment-create")
        pay_data = {
            "membership": membership_id,
            "payment_method": "momo"
        }
        response = self.client.post(pay_url, pay_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payment_id = response.data["id"]
        
        # Confirm payment
        confirm_url = reverse("payment-confirm", args=[payment_id])
        response = self.client.post(confirm_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify membership status is now ACTIVE
        membership_obj = UserMembership.objects.get(id=membership_id)
        self.assertEqual(membership_obj.status, MembershipStatus.ACTIVE)
        
        # Now booking should succeed
        response = self.client.post(booking_url, booking_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


from gym_booking_backend.infrastructure.models import PTPackage, TrainerSchedule, UserPTPackage, PTBooking
from gym_booking_backend.application.services import pt_booking_service
from gym_booking_backend.domain.exceptions import PTBookingException

class PTBookingTests(APITestCase):
    def setUp(self):
        # Create standard Member
        self.member_user = User.objects.create_user(
            username="pt_member_test",
            password="testpassword",
            email="pt_member@test.com"
        )
        self.member_profile = Profile.objects.create(
            user=self.member_user,
            full_name="PT Member Test",
            role=UserRole.MEMBER
        )

        # Create Trainer
        self.trainer_user = User.objects.create_user(
            username="pt_trainer_test",
            password="testpassword",
            email="pt_trainer@test.com"
        )
        self.trainer_profile = Profile.objects.create(
            user=self.trainer_user,
            full_name="PT Trainer Test",
            role=UserRole.TRAINER
        )
        self.trainer_record = Trainer.objects.create(
            user=self.trainer_user,
            name="PT Trainer Test",
            email="pt_trainer@test.com",
            phone="123456789",
            specialty="Pilates",
            status="active"
        )

        # Active Membership Package & Membership
        self.membership_package = MembershipPackage.objects.create(
            name="Gym Pass",
            price=150000.00,
            duration_days=30
        )
        self.membership = UserMembership.objects.create(
            user=self.member_user,
            package=self.membership_package,
            start_date=timezone.now().date() - timedelta(days=2),
            end_date=timezone.now().date() + timedelta(days=20),
            status=MembershipStatus.ACTIVE
        )

        # PT Package
        self.pt_package = PTPackage.objects.create(
            name="PT Gold 12 Sessions",
            price=5000000.00,
            duration_days=30,
            total_sessions=12,
            is_active=True
        )

        # Trainer Schedule (Available Monday, Wednesday, Friday from 08:00 to 20:00)
        TrainerSchedule.objects.create(trainer=self.trainer_record, weekday=0, start_time="08:00", end_time="20:00")
        TrainerSchedule.objects.create(trainer=self.trainer_record, weekday=2, start_time="08:00", end_time="20:00")
        TrainerSchedule.objects.create(trainer=self.trainer_record, weekday=4, start_time="08:00", end_time="20:00")

    def test_preview_and_create_pt_bookings(self):
        start_date = timezone.now().date() + timedelta(days=1)
        # Find the next Monday
        while start_date.weekday() != 0:
            start_date += timedelta(days=1)

        # Preview PT sessions
        previews = pt_booking_service.preview_monthly_pt_bookings(
            user=self.member_user,
            package_id=self.pt_package.id,
            trainer_id=self.trainer_record.id,
            start_date=start_date,
            selected_weekdays=[0, 2, 4], # Mon, Wed, Fri
            start_time="10:00",
            end_time="11:00"
        )
        self.assertEqual(len(previews), 12)
        for preview in previews:
            self.assertTrue(preview["is_valid"])

        # Create bookings
        user_package, bookings = pt_booking_service.create_monthly_pt_bookings(
            user=self.member_user,
            package_id=self.pt_package.id,
            trainer_id=self.trainer_record.id,
            start_date=start_date,
            selected_weekdays=[0, 2, 4],
            start_time="10:00",
            end_time="11:00"
        )

        self.assertEqual(user_package.total_sessions, 12)
        self.assertEqual(user_package.remaining_sessions, 12)
        self.assertEqual(len(bookings), 12)
        self.assertEqual(PTBooking.objects.filter(user_pt_package=user_package).count(), 12)

        # Test overlap checking
        with self.assertRaises(PTBookingException):
            pt_booking_service.create_monthly_pt_bookings(
                user=self.member_user,
                package_id=self.pt_package.id,
                trainer_id=self.trainer_record.id,
                start_date=start_date,
                selected_weekdays=[0, 2, 4],
                start_time="10:00",
                end_time="11:00"
            )

    def test_complete_and_cancel_pt_booking(self):
        start_date = timezone.now().date() + timedelta(days=1)
        while start_date.weekday() != 0:
            start_date += timedelta(days=1)

        user_package, bookings = pt_booking_service.create_monthly_pt_bookings(
            user=self.member_user,
            package_id=self.pt_package.id,
            trainer_id=self.trainer_record.id,
            start_date=start_date,
            selected_weekdays=[0, 2, 4],
            start_time="10:00",
            end_time="11:00"
        )
        first_booking = bookings[0]

        # Complete booking
        pt_booking_service.complete_pt_booking(first_booking.id)
        first_booking.refresh_from_db()
        user_package.refresh_from_db()
        self.assertEqual(first_booking.status, "completed")
        self.assertEqual(user_package.used_sessions, 1)
        self.assertEqual(user_package.remaining_sessions, 11)

        # Cancel other booking
        second_booking = bookings[1]
        pt_booking_service.cancel_pt_booking(second_booking.id)
        second_booking.refresh_from_db()
        self.assertEqual(second_booking.status, "cancelled")

        # Cancel package
        pt_booking_service.cancel_user_pt_package(user_package.id)
        user_package.refresh_from_db()
        self.assertEqual(user_package.status, "cancelled")
        # Remaining non-completed active bookings should be cancelled
        self.assertEqual(PTBooking.objects.filter(user_pt_package=user_package, status="confirmed").count(), 0)


