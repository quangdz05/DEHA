class GymException(Exception):
    default_message = "Gym business rule violated."

    def __init__(self, message=None):
        super().__init__(message or self.default_message)


class BookingException(GymException):
    default_message = "Booking is invalid."


class ScheduleFullException(BookingException):
    default_message = "Schedule is full."


class ScheduleAlreadyStartedException(BookingException):
    default_message = "Schedule has already started."


class DuplicateBookingException(BookingException):
    default_message = "You already booked this schedule."


class OverlapBookingException(BookingException):
    default_message = "You already have another booking in this time range."


class MembershipRequiredException(BookingException):
    default_message = "Active membership is required."


class InvalidScheduleException(GymException):
    default_message = "Schedule is invalid."


class PaymentException(GymException):
    default_message = "Payment is invalid."


class ReviewException(GymException):
    default_message = "Review is invalid."


class PTBookingException(GymException):
    default_message = "PT Booking business rule violated."


