import logging

import panel as pn
from view.cards.content_card import ContentCard

logger = logging.getLogger(__name__)


class ModelParametersCard(ContentCard):
    CARD_WIDTH = 500

    def draw(self, model_params):
        card = pn.Card(
            styles={"background": "lightgrey", "overflow": "auto"},
            width=self.CARD_WIDTH,
            hide_header=True,
        )

        if model_params.get("Error"):
            card.objects = [
                pn.pane.Markdown(
                    """ ### Es konnten keine Modellparameter ermittelt werden """
                )
            ]
            return card

        coverage = model_params["Evaluate-ARDCollabMatrix"]["pct_catalog_coverage"]
        coverage_weight = model_params["Statische Hyperparameter"]["Coverage-Gewicht"]
        watchtime = model_params["Evaluate-ARDCollabMatrix"]["pct_watch_time"]
        watchtime_weight = model_params["Statische Hyperparameter"]["Watchtime-Gewicht"]

        card.objects = [
            pn.pane.Markdown(f"""
                ### Modellmetadaten:
                **Erzeugt am:** {model_params['Metadata']['created']}
                **Modellbeschreibung:** {model_params['Metadata']['description']}
                ### Preprocessing Parameter:
                **Nutzungshistorie in Tagen:** {model_params['Preprocess-ARDCollabMatrix']['n_days']}
                **Train Ratio:** {model_params['Preprocess-ARDCollabMatrix']['train_ratio']}
                **Test Ratio:** {model_params['Preprocess-ARDCollabMatrix']['test_ratio']}
                **Validation Ratio:** {model_params['Preprocess-ARDCollabMatrix']['validation_ratio']}
                **Mindestanzahl Interaktionen:** {model_params['Preprocess-ARDCollabMatrix']['min_number_of_interactions']}
                **Letzte x Events:** {model_params['Preprocess-ARDCollabMatrix']['latest_x_events']}
                **Zielwert-Spalte:** {model_params['Preprocess-ARDCollabMatrix']['model_target_column']}
                ### Tuning Hyperparameter:
                **Alpha:** {model_params['Tuning-Hyperparameter']['alpha']}
                **Regularization:** {model_params['Tuning-Hyperparameter']['regularization']}
                **Factors:** {model_params['Tuning-Hyperparameter']['factors']}
                ### Statische Hyperparameter:
                **Coverage Gewicht:** { coverage_weight }
                **Watchtime Gewicht:** { watchtime_weight}
                **Random State:** {model_params['Statische Hyperparameter']['Random State']}
                ### Evaluations-Metriken:
                **Coverage:** { coverage}
                **Watchtime:** { watchtime}
                **Zielmetrik-Name:** {model_params['Trainings-Metriken']['Zielmetrik-Name']}
                **Zielmetrik-Wert:** { coverage_weight * coverage + watchtime_weight * watchtime }
                """)
        ]
        return card
