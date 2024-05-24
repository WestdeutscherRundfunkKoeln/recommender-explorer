import logging

import panel as pn
from controller.reco_controller import RecommendationController
from dto.content_item import ContentItemDto
from util.dto_utils import get_primary_idents

logger = logging.getLogger(__name__)


class ContentCard:
    def __init__(self, config):
        self.config = config
        self.controller = RecommendationController(self.config)

    def draw(self, content_dto: ContentItemDto, card):
        id_key, id_val = get_primary_idents(self.config)

        base_card_objects = [
            pn.pane.Markdown(f"""
                       #### {content_dto.title}
                       **Erzählweise:** {self.controller.get_upper_genres_and_subgenres(content_dto.genreCategory)}
                       **Genre:** {content_dto.genreCategory}
                       **Inhalt:** {self.controller.get_upper_genres_and_subgenres(content_dto.subgenreCategories)}
                       **Subgenre:** {', '.join(set(content_dto.subgenreCategories))}
                       **Themen:** {', '.join(set(content_dto.thematicCategories))}
                       **Sendereihe:** {content_dto.showTitle}
                       **Datum:** {content_dto.createdFormatted}
                       **{id_key}:** {content_dto.__getattribute__(id_val)}
                """),
            content_dto.description,
        ]

        card.objects = card.objects + base_card_objects
        return card
