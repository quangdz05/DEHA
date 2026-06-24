from gym_booking_backend.infrastructure.repositories.user_repository import DjangoUserRepository
from gym_booking_backend.infrastructure.repositories.booking_repository import DjangoBookingRepository
from gym_booking_backend.infrastructure.repositories.class_repository import DjangoClassRepository
from gym_booking_backend.infrastructure.repositories.membership_repository import DjangoMembershipRepository
from gym_booking_backend.infrastructure.repositories.payment_repository import DjangoPaymentRepository
from gym_booking_backend.infrastructure.repositories.profile_repository import DjangoProfileRepository
from gym_booking_backend.infrastructure.repositories.review_repository import DjangoReviewRepository
from gym_booking_backend.infrastructure.repositories.schedule_repository import DjangoScheduleRepository
from gym_booking_backend.infrastructure.repositories.trainer_repository import DjangoTrainerRepository
from gym_booking_backend.infrastructure.repositories.pt_repository import DjangoPTRepository
from gym_booking_backend.infrastructure.repositories.invoice_repository import DjangoInvoiceRepository

from gym_booking_backend.application.services.auth_service import AuthService
from gym_booking_backend.application.services.booking_service import BookingService
from gym_booking_backend.application.services.catalog_service import CatalogService
from gym_booking_backend.application.services.membership_service import MembershipService
from gym_booking_backend.application.services.payment_service import PaymentService
from gym_booking_backend.application.services.profile_service import ProfileService
from gym_booking_backend.application.services.pt_booking_service import PTBookingService
from gym_booking_backend.application.services.review_service import ReviewService
from gym_booking_backend.application.services.schedule_service import ScheduleService


class DIContainer:
    def __init__(self):
        # ── 1. Repositories ──────────────────────────────────────────
        self.user_repository = DjangoUserRepository()
        self.booking_repository = DjangoBookingRepository()
        self.class_repository = DjangoClassRepository()
        self.membership_repository = DjangoMembershipRepository()
        self.payment_repository = DjangoPaymentRepository()
        self.profile_repository = DjangoProfileRepository()
        self.review_repository = DjangoReviewRepository()
        self.schedule_repository = DjangoScheduleRepository()
        self.trainer_repository = DjangoTrainerRepository()
        self.pt_repository = DjangoPTRepository()
        self.invoice_repository = DjangoInvoiceRepository()

        # ── 2. Services (inject dependencies via constructor) ─────────
        self.auth_service = AuthService(
            user_repo=self.user_repository,
            profile_repo=self.profile_repository,
            trainer_repo=self.trainer_repository,
        )

        self.booking_service = BookingService(
            booking_repo=self.booking_repository,
            schedule_repo=self.schedule_repository,
            trainer_repo=self.trainer_repository,
            membership_repo=self.membership_repository,
        )

        self.catalog_service = CatalogService(
            class_repo=self.class_repository,
            trainer_repo=self.trainer_repository,
        )

        self.membership_service = MembershipService(
            membership_repo=self.membership_repository,
            invoice_repo=self.invoice_repository,
            payment_repo=self.payment_repository,
        )

        self.payment_service = PaymentService(
            payment_repo=self.payment_repository,
            membership_repo=self.membership_repository,
            invoice_repo=self.invoice_repository,
            booking_repo=self.booking_repository,
        )

        self.profile_service = ProfileService(
            profile_repo=self.profile_repository,
        )

        self.pt_booking_service = PTBookingService(
            pt_repo=self.pt_repository,
            membership_repo=self.membership_repository,
            trainer_repo=self.trainer_repository,
        )

        self.review_service = ReviewService(
            review_repo=self.review_repository,
            trainer_repo=self.trainer_repository,
            class_repo=self.class_repository,
            booking_repo=self.booking_repository,
        )

        self.schedule_service = ScheduleService(
            schedule_repo=self.schedule_repository,
        )


# Global DI Container instance
container = DIContainer()
