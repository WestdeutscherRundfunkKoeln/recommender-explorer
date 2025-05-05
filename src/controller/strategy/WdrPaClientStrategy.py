from controller.strategy.BrClientStrategy import BrClientStrategy


class WdrPaClientStrategy(BrClientStrategy):
    def map_refinement_direction(self, direction):
        if direction == "more similar":
            return "more similar embeddings"
        return direction

    def get_weights_by_type(self):
        return {
            "Semantic": {"semanticWeight": 0.35, "timeWeight": 0.2},
            "Diverse": {"diversityWeight": 0.7, "timeWeight": 0.2},
            "Temporal": {"timeWeight": 0.5}
        }

    def restructure_filter_state(self, filter_state):
        filter_state = self._extract_weights(filter_state)
        return self._flatten_simple_keys(filter_state)

    def _extract_weights(self, filter_state):
        weights = []
        keywords = ["beitrag", "audio", "video"]
        for key in list(filter_state.keys()):
            if key in keywords:
                value = filter_state.pop(key)
                if value != 0:
                    weights.append({"type": key, "weight": value})
        if weights:
            filter_state["weights"] = weights
        return filter_state
