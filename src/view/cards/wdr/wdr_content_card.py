import panel as pn
import logging
from dto.wdr_content_item import WDRContentItemDto

logger = logging.getLogger(__name__)
class WDRContentCard():

    def __init__(self, config):
        self.config = config

    def draw(self, content_dto: WDRContentItemDto, card):

        base_card_objects = [
                pn.pane.Markdown(f"""
                       #### {content_dto.title}
                       **Themen:** {', '.join(set(content_dto.thematicCategories))}
                       **Datentyp:** {content_dto.type} 
                       **Keywords:** {', '.join(set(content_dto.keywords))}
                       **Strukturpfad:** {content_dto.structurePath}
                       **External ID:** {content_dto.externalid} 
                       **Sophora ID:** {content_dto.sophoraid}
                       **Datum:** {content_dto.availableFrom}
                """),
                content_dto.description
        ]

        card.objects = card.objects + base_card_objects
        return card
