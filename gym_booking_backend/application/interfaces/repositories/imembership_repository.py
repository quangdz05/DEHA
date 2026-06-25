from abc import ABC, abstractmethod


class IMembershipRepository(ABC):
    @abstractmethod
    def get_package_by_id(self, package_id):
        pass

    @abstractmethod
    def get_active_packages(self):
        pass

    @abstractmethod
    def get_active_membership(self, user):
        pass

    @abstractmethod
    def has_active_membership(self, user):
        pass

    @abstractmethod
    def create_user_membership(self, user, package, start_date, end_date):
        pass

    @abstractmethod
    def get_user_membership_by_id(self, user, membership_id):
        pass

    @abstractmethod
    def get_user_memberships(self, user):
        pass

    @abstractmethod
    def expire_memberships_before(self, date):
        pass

    @abstractmethod
    def has_active_or_pending_membership(self, user):
        pass
