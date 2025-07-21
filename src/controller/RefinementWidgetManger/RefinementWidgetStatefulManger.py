from abc import ABC
from controller.RefinementWidgetManger.RefinementWidgetRequestManger import RefinementWidgetRequestManger

class RefinementWidgetStatefulManger(RefinementWidgetRequestManger, ABC):
    def __init__(self):
        self.reset()

    def prepare_request(self, reco_filter, current_ref_id):
        refinement_type = reco_filter.pop("refinementType", "")
        reco_filter["utilities"] = [
            {"utility": key, "weight": value}
            for key, value in self.weights.get(refinement_type, {}).items()
        ]

        if (refinement_type == self.previous_ref_value and
            current_ref_id == self.previous_ref_id and  "refinement" in reco_filter):
            reco_filter["refinement"]["previousExternalIds"] = self.previous_external_ids
            reco_filter["utilities"] = self.utilities


        elif (refinement_type == self.previous_ref_value and
            current_ref_id == self.previous_ref_id and self.utilities):
            reco_filter["utilities"] = self.utilities


        else:
            self.reset()

        # Update
        self.previous_ref_value = refinement_type
        self.previous_ref_id = current_ref_id

        return reco_filter

    def process_response(self, ids, utilities):
        self.previous_external_ids = ids
        self.utilities = utilities

    def reset(self):
        self.previous_external_ids = []
        self.previous_ref_value = ""
        self.previous_ref_id = ""
        self.utilities = []

    def get_weights_by_type(self):
        raise NotImplementedError

    def restructure_filter_state(self, filter_state):
        # Move weights (only add non-zero) and remove from top level
        weights = []
        for key in ["beitrag", "audio", "video"]:
            value = filter_state.get(key)
            if value not in [0, "", None]:
                weights.append({"type": key, "weight": value})
                filter_state.pop(key, None)  # Remove after adding to weights

        # Only add weights to filter_state if there are valid weights
        if weights:
            filter_state["weights"] = weights

        # Remove keys with value 0 or ""
        for key in list(filter_state.keys()):
            if filter_state[key] == 0 or filter_state[key] == "":
                filter_state.pop(key)

        # Move remaining valid flat keys into "filter", removing them from top level
        flat_keys = {}
        for key in list(filter_state.keys()):
            if key != "refinementType" and not isinstance(filter_state[key], (dict, list)):
                value = filter_state.pop(key)

                # Special handling for "excludedIds" to always be a list
                if key == "excludedIds":
                    value = [value]

                flat_keys[key] = value

        if flat_keys:
            filter_state["filters"] = flat_keys

        return filter_state

    def check_threshold(self, widget):
        """Disables the active button if threshold conditions are met."""
        weights = {u["utility"]: u["weight"] for u in self.utilities}
        semantic_weight = weights.get("semanticWeight", 0)
        tag_weight = weights.get("tagWeight", 0)

        if any(w in {0, 1} for w in weights.values()) or (semantic_weight + tag_weight == 1):
            widget.disable_active_button()

    def enable_all_buttons(self, widget):
        widget.enable_all_buttons()

    def reset_refinement_widget(self, widget):
        """
        Safely resets the state of the refinement widget.
        """
        self.reset()
        if hasattr(widget, "alert"):
            widget.alert.visible = False
        if hasattr(widget, "btn1"):
            widget.btn1.disabled = False
        if hasattr(widget, "btn2"):
            widget.btn2.disabled = False

    def reset_all(self,widget):
        # gets triggered when we change the active accordion of a specific model type
        self.reset()
        self.reset_refinement_widget(widget)