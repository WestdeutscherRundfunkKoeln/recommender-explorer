import panel as pn
import logging
from dto.content_item import ContentItemDto
from controller.reco_controller import RecommendationController
from util.dto_utils import get_primary_idents
from view.RecoExplorerApp import RecoExplorerApp

logger = logging.getLogger(__name__)


class ContentCard:
    def __init__(
        self,
        config,
        reco_explorer_app_instance: RecoExplorerApp | None = None,
        height=None,
        width=None,
        image_height=None,
    ):
        self.config = config
        self.reco_explorer_app_instance = reco_explorer_app_instance
        self.controller = RecommendationController(self.config)
        self.card_height = height if height is not None else 600
        self.card_width = width if width is not None else 300
        self.card_image_height = image_height if width is not None else 75

    def draw(self, content_dto: ContentItemDto, card):
        assert self.reco_explorer_app_instance is not None, (
            "RecoExplorerApp instance must be provided"
        )
        id_key, id_val = get_primary_idents(self.config)

        base_card_objects = [
            pn.pane.HTML(f"""
                       <h4>{content_dto.title}</h4>
                       <p> 
                       <strong>Erzählweise:</strong> {self.controller.get_upper_genres_and_subgenres(content_dto.genreCategory)} <br>
                       <strong>Genre:</strong> {content_dto.genreCategory}<br>
                       <strong>Inhalt:</strong> {self.controller.get_upper_genres_and_subgenres(content_dto.subgenreCategories)} <br>
                       <strong>Subgenre:</strong> {", ".join(set(content_dto.subgenreCategories))}<br>
                       <strong>Themen:</strong> {", ".join(set(content_dto.thematicCategories))}<br>
                       <strong>Show-Titel:</strong> {content_dto.showTitle}<br>
                       <strong>Datum:</strong> {content_dto.createdFormatted}<br>
                       <strong>{id_key}:</strong> {content_dto.__getattribute__(id_val)}<br>
                        </p>
                """),
            content_dto.description,
        ]

        card.objects = card.objects + base_card_objects
        return card
