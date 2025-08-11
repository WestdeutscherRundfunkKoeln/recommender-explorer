from controller.RefinementWidgetManger.RefinementWidgetStatefulManger import RefinementWidgetStatefulManger

class M14RefinementWidgetRequestManger(RefinementWidgetStatefulManger):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.weights = {
            "Semantic": {"semanticWeight": 0.35, "timeWeight": 0.2},
            "Diverse": {"diversityWeight": 0.7, "timeWeight": 0.2},
            "Temporal": {"timeWeight": 0.5}
        }

    def map_refinement_direction(self, direction):
        # Specific logic for WDR_PA
        if direction == "more similar":
            return "more similar embeddings"
        return direction
