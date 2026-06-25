from abc import ABC, abstractmethod


class IInvoiceRepository(ABC):
    @abstractmethod
    def create_invoice(self, user, invoice_number, total_amount, status):
        pass

    @abstractmethod
    def create_invoice_item(self, invoice, item_type, object_id, amount):
        pass

    @abstractmethod
    def get_invoice_item_by_membership(self, membership_id):
        pass

    @abstractmethod
    def get_invoice_item_by_class_fee(self, booking_id):
        pass
