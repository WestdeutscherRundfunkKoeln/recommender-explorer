from controller.RefinementWidgetManger.RefinementWidgetStatefulManger import RefinementWidgetStatefulManger

class WdrPaRefinementWidgetRequestManger(RefinementWidgetStatefulManger):
    def get_weights_by_type(self):
        return {
            "Semantic": {"semanticWeight": 0.35, "timeWeight": 0.2},
            "Diverse": {"diversityWeight": 0.7, "timeWeight": 0.2},
            "Temporal": {"timeWeight": 0.5}
        }

    def map_refinement_direction(self, direction):
        # Specific logic for WDR_PA
        if direction == "more similar":
            return "more similar embeddings"
        return direction
