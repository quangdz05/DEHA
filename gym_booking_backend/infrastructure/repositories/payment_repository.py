from gym_booking_backend.infrastructure.models import Payment


def get_payment_by_id(payment_id):
    return Payment.objects.select_related("membership", "membership__package", "invoice").filter(id=payment_id).first()


def get_user_payments(user):
    return Payment.objects.select_related("membership", "membership__package", "invoice").filter(user=user)


def create_payment(user, membership, amount, payment_method, transaction_code=None, invoice=None):
    return Payment.objects.create(
        user=user,
        membership=membership,
        amount=amount,
        payment_method=payment_method,
        transaction_code=transaction_code,
        invoice=invoice,
    )

