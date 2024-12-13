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

    domain_mapping = {"wdr.de": "https://www1.wdr.de"}

    def __init__(
        self,
        config,
        reco_explorer_app_instance: RecoExplorerApp | None = None,
        height=None,
        width=None,
    ):
        self.config = config
        self.reco_explorer_app_instance = reco_explorer_app_instance
        self.card_height = height if height is not None else 600
        self.card_width = width if width is not None else 300

    def draw(
        self,
        content_dto: WDRContentItemDto,
        card: pn.Card,
        button: pn.widgets.Button | None = None,
        extra_data: pn.widgets.Button | None = None,
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
                       **Sophora ID:** [{content_dto.cmsId}](https://{content_dto.domain}{content_dto.structurePath}/{content_dto.cmsId}.html)
                """),
        ]

        if button:
            base_card_objects.insert(1, button)

        if extra_data:
            base_card_objects.append(extra_data)

        card.objects = (
            cast(list[pn.viewable.Viewable], card.objects) + base_card_objects
        )
        return card
