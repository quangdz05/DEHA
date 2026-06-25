from gym_booking_backend.infrastructure.models import Payment
from gym_booking_backend.application.interfaces.repositories.ipayment_repository import IPaymentRepository


class DjangoPaymentRepository(IPaymentRepository):
    def get_payment_by_id(self, payment_id):
        return Payment.objects.select_related("membership", "membership__package", "invoice").filter(id=payment_id).first()

    def get_user_payments(self, user):
        return Payment.objects.select_related("membership", "membership__package", "invoice").filter(user=user)

    def create_payment(self, user, membership, amount, payment_method, transaction_code=None, invoice=None):
        return Payment.objects.create(
            user=user,
            membership=membership,
            amount=amount,
            payment_method=payment_method,
            transaction_code=transaction_code,
            invoice=invoice,
        )


payment_repository = DjangoPaymentRepository()
