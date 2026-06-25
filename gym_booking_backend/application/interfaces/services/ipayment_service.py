from abc import ABC, abstractmethod
from gym_booking_backend.domain.result import Result


class IPaymentService(ABC):
    @abstractmethod
    def create_payment(self, user, membership_id, payment_method) -> Result:
        pass

    @abstractmethod
    def confirm_payment(self, payment_id) -> Result:
        pass

    @abstractmethod
    def fail_payment(self, payment_id) -> Result:
        pass

    @abstractmethod
    def refund_payment(self, payment_id) -> Result:
        pass

    @abstractmethod
    def get_my_payments(self, user) -> Result:
        pass

    @abstractmethod
    def create_trainer_booking_payment(self, user, trainer_booking_id, payment_method) -> Result:
        pass
