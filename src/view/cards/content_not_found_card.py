import panel as pn
from datetime import datetime
from dto.user_item import UserItemDto

class NotFoundCard():

    def __init__(self, config, reco_explorer_app_instance=None):
        self.config = config
        self.reco_explorer_app_instance = reco_explorer_app_instance

    def draw(self, user_dto: UserItemDto, nr, model, model_config, modal_func):

        card = pn.Card(
            styles={'background': 'lightgrey', 'overflow': 'auto'},
            margin=5,
            height=600,
            hide_header=True
        )

        card_objects = [
           pn.pane.Markdown(f""" #### Keine Empfehlungen für diesen Benutzer oder dieses Item in diesem Modell""")
        ]
        card.objects = card_objects
        return card
