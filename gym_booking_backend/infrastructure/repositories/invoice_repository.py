from gym_booking_backend.application.interfaces.repositories.iinvoice_repository import IInvoiceRepository
from gym_booking_backend.infrastructure.models import Invoice, InvoiceItem


class DjangoInvoiceRepository(IInvoiceRepository):
    def create_invoice(self, user, invoice_number, total_amount, status):
        return Invoice.objects.create(
            user=user,
            invoice_number=invoice_number,
            total_amount=total_amount,
            status=status,
        )

    def create_invoice_item(self, invoice, item_type, object_id, amount):
        return InvoiceItem.objects.create(
            invoice=invoice,
            item_type=item_type,
            object_id=object_id,
            amount=amount,
        )

    def get_invoice_item_by_membership(self, membership_id):
        from gym_booking_backend.domain.constants import InvoiceItemType
        return (
            InvoiceItem.objects.select_related("invoice")
            .filter(item_type=InvoiceItemType.MEMBERSHIP, object_id=membership_id)
            .first()
        )

    def get_invoice_item_by_class_fee(self, booking_id):
        from gym_booking_backend.domain.constants import InvoiceItemType
        return (
            InvoiceItem.objects.select_related("invoice")
            .filter(item_type=InvoiceItemType.CLASS_FEE, object_id=booking_id)
            .first()
        )


invoice_repository = DjangoInvoiceRepository()
