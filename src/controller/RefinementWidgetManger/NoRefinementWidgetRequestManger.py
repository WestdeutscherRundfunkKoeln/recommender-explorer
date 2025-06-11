from controller.RefinementWidgetManger.RefinementWidgetRequestManger import RefinementWidgetRequestManger

class NoRefinementWidgetRequestManger(RefinementWidgetRequestManger):
    def prepare_request(self, reco_filter, current_ref_id):
        return reco_filter  # No modification

    def process_response(self, ids, utilities):
        pass  # No state to update

    def reset(self):
        pass  # No state to reset

    def restructure_filter_state(self, filter_state):
        return filter_state  # Return as-is

    def map_refinement_direction(self, direction):
        pass  # No mapping needed

    def get_weights_by_type(self):
        return {}  # No weights configured

    def reset_all(self,widget):
        pass