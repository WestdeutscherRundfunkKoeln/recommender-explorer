import constants
from dataclasses import dataclass
from dto.content_item import ContentItemDto
from datetime import datetime

@dataclass
class HistoryItemDto(ContentItemDto):
    @property
    def viewer(self) -> str:
        self._viewer = 'ContentHistoryCard@view.cards.floatpanel_history_card'
        return self._viewer
