from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class BookingEntity:
    id: int
    user_id: int
    schedule_id: int
    booking_code: str
    status: str


@dataclass(frozen=True)
class ScheduleEntity:
    id: int
    gym_class_id: int
    room_id: int
    start_time: datetime
    end_time: datetime
    max_participants: int
    current_participants: int
    status: str


@dataclass(frozen=True)
class MembershipEntity:
    id: int
    user_id: int
    package_id: int
    start_date: date
    end_date: date
    status: str
    price: Decimal | None = None

