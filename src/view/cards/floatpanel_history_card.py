import logging

import panel as pn
from dto.content_item import ContentItemDto
from view.cards.content_card import ContentCard

logger = logging.getLogger(__name__)


class ContentHistoryCard(ContentCard):
    CARD_HEIGHT = 470
    IMAGE_HEIGHT = 75

    def __init__(self, config):
        super().__init__(config)

    def draw(self, content_dto: ContentItemDto, nr, model):
        child_objects = [
            pn.pane.HTML(
                f"""<img style="height: { self.IMAGE_HEIGHT }px; display: block; margin-left: auto; margin-right: auto; align:center" src={content_dto.teaserimage}></img>"""
            ),
            pn.pane.Markdown(f""" ### Video {nr} """),
        ]

        card = pn.Card(
            styles={"background": "lightgrey", "overflow": "auto"},
            margin=5,
            height=self.CARD_HEIGHT,
            hide_header=True,
        )

        card.objects = child_objects

        return super().draw(content_dto, card)
