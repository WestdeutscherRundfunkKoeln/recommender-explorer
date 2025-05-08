from controller.RefinementWidgetManger.RefinementWidgetStatefulManger import RefinementWidgetStatefulManger

class BrRefinementWidgetRequestManger(RefinementWidgetStatefulManger):
    def get_weights_by_type(self):
        return {
            "Semantic": {"semanticWeight": 0.35, "tagWeight": 0.35, "timeWeight": 0.2, "localTrendWeight": 0.1},
            "Diverse": {"diversityWeight": 0.7, "timeWeight": 0.2, "localTrendWeight": 0.1},
            "Temporal": {"timeWeight": 0.5, "localTrendWeight": 0.5}
        }

    def map_refinement_direction(self, direction):
        return direction