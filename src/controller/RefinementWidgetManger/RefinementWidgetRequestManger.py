from abc import ABC, abstractmethod

class RefinementWidgetRequestManger(ABC):
    @abstractmethod
    def prepare_request(self, reco_filter, current_ref_id):
        """Prepare and possibly mutate the reco_filter before sending the request."""
        pass

    @abstractmethod
    def process_response(self, ids, utilities):
        """Handle post-response state updates (e.g. caching IDs/utilities)."""
        pass

    @abstractmethod
    def reset(self):
        """Reset any internal state related to refinement handling."""
        pass

    @abstractmethod
    def restructure_filter_state(self, filter_state):
        """Modify the filter_state (e.g. flatten or reorganize keys)."""
        pass

    @abstractmethod
    def map_refinement_direction(self, direction):
        """Translate user-facing direction labels to internal values."""
        pass

    @abstractmethod
    def get_weights_by_type(self):
        """Return the configured weights for each refinement type."""
        pass
