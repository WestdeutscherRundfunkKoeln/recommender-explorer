import logging
from typing import cast
from datetime import datetime

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
        try:
            formatted_date = datetime.fromisoformat(content_dto.availableFrom).strftime(
                "%d-%b-%Y %H:%M"
            )
        except ValueError:
            formatted_date = content_dto.availableFrom
        base_card_objects: list[pn.viewable.Viewable] = [
            pn.pane.HTML(f"""
                        <h4>{content_dto.title}</h4>
                        <p>
                       <strong>Datentyp:</strong> {content_dto.type.title()} {self.type_icon.get(content_dto.type, "")} <br>
                       <strong>Datum:</strong> {formatted_date}<br>
                       <strong>Strukturpfad:</strong> {content_dto.structurePath}<br>
                       <strong>External ID:</strong> {content_dto.externalid}<br>
                       <strong>Themen:</strong> {", ".join(set(content_dto.thematicCategories))}<br>
                       <strong>Keywords:</strong> {", ".join(set(content_dto.keywords))}<br>
                       <strong>Sophora ID:</strong> <a href=https://{content_dto.domain}{content_dto.structurePath}/{content_dto.cmsId}.html>{content_dto.cmsId}</a><br>
                        </p>
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

    def get_background_color(self, content_dto, model, model_config):
        return self.config[model_config][content_dto.provenance][model]["reco_color"]
