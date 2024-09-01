import panel as pn
from datetime import datetime
from dto.user_item import UserItemDto

class UserCard():

    def __init__(self, config, *kwargs):
        self.config = config

    def draw(self, user_dto: UserItemDto, nr, model, model_config, modal_func):

        card_optional_objects = []

        card = pn.Card(
            styles={ 'background': self.config[model_config][user_dto.provenance][model]['start_color'] },
            margin=5,
            height=600,
            hide_header=True
        )

        if user_dto.last_active:
            last_active = datetime.fromtimestamp(user_dto.last_active/1000.0).strftime("%d/%m/%Y, %H:%M:%S")
        else:
            last_active = '- unbekannt -'

        if user_dto.history:
            history_button = pn.widgets.Button(name='Historie anzeigen', button_type='primary')
            history_button.params = {
                'item': user_dto,
                'button': 'history_button'
            }
            history_button.on_click(modal_func)
            card_optional_objects.append(history_button)

        if 1: #user_dto.model_params:
            params_button = pn.widgets.Button(name='Modellparameter anzeigen', button_type='primary')
            params_button.params = {
                'item': user_dto,
                'button': 'params_button'
            }
            params_button.on_click(modal_func)
            card_optional_objects.append(params_button)

        card_objects = [
            pn.pane.Markdown(f""" ### Modell: { model } """),
            pn.pane.PNG(user_dto.avatar, width=130, height=150, align='center'),
            pn.pane.Markdown(f"""
            #### User id: { user_dto.id } <br>
            #### Nutzungs-Typus: { user_dto.source }  <br>
            **Typus-Wert:** { user_dto.source_value }
            **Zuletzt aktiv:** { last_active }
            **Zuletzt angesehene Genres:** { ",".join(user_dto.last_genres ) }
            """)
        ]

        card.objects = card_objects + card_optional_objects

        return card