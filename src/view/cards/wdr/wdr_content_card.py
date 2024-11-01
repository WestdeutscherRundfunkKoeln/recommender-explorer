import logging

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

    def __init__(self, config, reco_explorer_app_instance: RecoExplorerApp = None):
        self.config = config
        self.reco_explorer_app_instance = reco_explorer_app_instance

    def draw(
        self,
        content_dto: WDRContentItemDto,
        card,
        button: pn.widgets.Button or None = None,
    ):
        base_card_objects = [
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
            pn.pane.Markdown(f"""
            ***
            ##### {content_dto.title}
            {" ".join(content_dto.longDescription.split(" ")[:500])}...
            """),
        ]

        if button:
            base_card_objects.insert(1, button)

        card.objects = card.objects + base_card_objects
        return card
