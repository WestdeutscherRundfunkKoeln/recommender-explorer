from abc import ABC, abstractmethod


class BaseDataAccessor(ABC):
    @abstractmethod
    def get_items_by_ids(self, ids):
        pass

    @abstractmethod
    def get_item_by_crid(self, crid):
        pass

    @abstractmethod
    def get_items_by_date(self, start_date, end_date, offset=0, size=-1):
        pass

    @abstractmethod
    def get_items_date_range_limits(self):
        pass

    @abstractmethod
    def get_top_k_vals_for_column(self, column, k):
        pass

    @abstractmethod
    def get_unique_vals_for_column(self, column, sort=True):
        pass
