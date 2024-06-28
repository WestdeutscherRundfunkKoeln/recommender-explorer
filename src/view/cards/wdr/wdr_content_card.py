import logging

import panel as pn
from dto.wdr_content_item import WDRContentItemDto

logger = logging.getLogger(__name__)


class WDRContentCard:
    type_icon = {
        "beitrag": "📰",
        "audio": "🔊",
        "video": "🎥",
    }

    domain_mapping = {"wdr.de": "https://www1.wdr.de"}

    def __init__(self, config):
        self.config = config

    def draw(self, content_dto: WDRContentItemDto, card):
        base_card_objects = [
            pn.pane.Markdown(f"""
                       #### {content_dto.title}
                       **Datentyp:** {self.type_icon.get(content_dto.type, content_dto.type)} 
                       **Datum:** {content_dto.availableFrom}
                       **Strukturpfad:** {content_dto.structurePath}
                       **External ID:** [{content_dto.externalid}]({self.config["reco_explorer_url_base"]}?externalId={content_dto.externalid}) 
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

        card.objects = card.objects + base_card_objects
        return card
