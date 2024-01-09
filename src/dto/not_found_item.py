import constants
from dataclasses import dataclass
from dto.item import ItemDto

@dataclass
class NotFoundDto(ItemDto):
    @property
    def viewer(self) -> str:
        self._viewer = 'NotFoundCard@view.cards.content_not_found_card'
        return self._viewer