from django.utils import timezone

from gym_booking_backend.domain.exceptions import GymException
from gym_booking_backend.infrastructure.repositories import membership_repository


def validate_membership_dates(start_date, end_date):
    if start_date < timezone.localdate():
        raise GymException("Membership start date cannot be in the past.")
    if end_date <= start_date:
        raise GymException("Membership end date must be after start date.")


def validate_user_has_no_active_membership(user):
    if membership_repository.has_active_membership(user):
        raise GymException("User already has an active membership.")

