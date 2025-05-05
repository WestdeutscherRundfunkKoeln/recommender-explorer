from controller.strategy.ClientStrategy import ClientStrategy


class BrClientStrategy(ClientStrategy):
    def restructure_filter_state(self, filter_state):
        return self._restructure(filter_state)

    def get_weights_by_type(self):
        return {
            "Semantic": {"semanticWeight": 0.35, "tagWeight": 0.35, "timeWeight": 0.2, "localTrendWeight": 0.1},
            "Diverse": {"diversityWeight": 0.7, "timeWeight": 0.2, "localTrendWeight": 0.1},
            "Temporal": {"timeWeight": 0.5, "localTrendWeight": 0.5}
        }

    def restructure_filter_state(self, filter_state):
        return self._flatten_simple_keys(filter_state)

    def _flatten_simple_keys(self, filter_state):
        flat_keys = {}
        for key, value in list(filter_state.items()):
            if key != "refinementType" and not isinstance(value, (dict, list)) and value not in (0, ""):
                flat_keys[key] = filter_state.pop(key)

        if flat_keys:
            filter_state["filter"] = flat_keys

        return filter_state
