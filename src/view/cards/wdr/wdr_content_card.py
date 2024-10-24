import logging
from typing import cast

import panel as pn
from dto.wdr_content_item import WDRContentItemDto
from view.RecoExplorerApp import RecoExplorerApp


logger = logging.getLogger(__name__)


class WDRContentCard:
    type_icon = {
        "beitrag": "📰",
        "audio": "🔊",
        "video": "🎥",
    }

    def __init__(
        self, config, reco_explorer_app_instance: RecoExplorerApp | None = None
    ):
        self.config = config
        self.reco_explorer_app_instance = reco_explorer_app_instance

    def draw(
        self,
        content_dto: WDRContentItemDto,
        card: pn.Card,
        button: pn.widgets.Button | None = None,
    ):
        base_card_objects: list[pn.viewable.Viewable] = [
            pn.pane.Markdown(f"""
                       #### {content_dto.title}
                       **Datentyp:** {content_dto.type.title()} {self.type_icon.get(content_dto.type, "")} 
                       **Datum:** {content_dto.availableFrom}
                       **Strukturpfad:** {content_dto.structurePath}
                       **External ID:** {content_dto.externalid}
                       **Themen:** {', '.join(set(content_dto.thematicCategories))}
                       **Keywords:** {', '.join(set(content_dto.keywords))}
                       **Sophora ID:** [{content_dto.sophoraid}](https://{content_dto.domain}{content_dto.structurePath}/{content_dto.sophoraid}.html)
                """),
            pn.pane.Markdown(f"""
            ***
            ##### {content_dto.title}
            {" ".join(content_dto.longDescription.split(" ")[:500])}...
            """),
        ]

        if button:
            base_card_objects.insert(1, button)

        card.objects = (
            cast(list[pn.viewable.Viewable], card.objects) + base_card_objects
        )
        return card
