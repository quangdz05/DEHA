from abc import ABC, abstractmethod


class IPaymentRepository(ABC):
    @abstractmethod
    def get_payment_by_id(self, payment_id):
        pass

    @abstractmethod
    def get_user_payments(self, user):
        pass

    @abstractmethod
    def create_payment(self, user, membership, amount, payment_method, transaction_code=None, invoice=None):
        pass
