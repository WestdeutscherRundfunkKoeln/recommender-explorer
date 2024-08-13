import logging

import panel as pn
from dto.pa_service_content_item import PaServiceContentItemDto

logger = logging.getLogger(__name__)


class PaServiceContentCard:
    type_icon = {
        "beitrag": "📰",
        "audio": "🔊",
        "video": "🎥",
    }

    domain_mapping = {"wdr.de": "https://www1.wdr.de"}

    def __init__(self, config, *kwargs):
        self.config = config

    def draw(self, content_dto: PaServiceContentItemDto, card):
        base_card_objects = [
            pn.pane.Markdown(f"""
                       #### {content_dto.title}
                       **Datentyp:** {self.type_icon.get(content_dto.contentType, content_dto.contentType)} 
                       **Datum:** {content_dto.availableFrom}
                       **Strukturpfad:** {content_dto.structureNodePath}
                       **External ID:** [{content_dto.externalId}]({self.config["reco_explorer_url_base"]}?externalId={content_dto.externalId}) 
                       **Sophora ID:** [{content_dto.sophoraId}](https://{content_dto.domain}{content_dto.structureNodePath}/{content_dto.sophoraId}.html)
                """),
            pn.pane.Markdown(f"""
            ***
            ##### {content_dto.title}
            {" ".join(content_dto.description.split(" ")[:500])}...
            """),
        ]

        card.objects = card.objects + base_card_objects
        return card
