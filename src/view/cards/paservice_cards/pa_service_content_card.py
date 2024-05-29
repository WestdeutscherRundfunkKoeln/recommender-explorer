import panel as pn
import logging
from dto.pa_service_content_item import PaServiceContentItemDto

logger = logging.getLogger(__name__)


class PaServiceContentCard:

    def __init__(self, config):
        self.config = config

    def draw(self, content_dto: PaServiceContentItemDto, card):

        base_card_objects = [
            pn.pane.Markdown(f"""
                       #### {content_dto.title}
                       **Datentyp:** {content_dto.contentType} 
                       **Strukturpfad:** {content_dto.structureNodePath}
                       **External ID:** {content_dto.externalId} 
                       **Sophora ID:** {content_dto.sophoraId}
                """),
            content_dto.description
        ]

        card.objects = card.objects + base_card_objects
        return card
