from dataclasses import dataclass

import constants
from dto.item import ItemDto


@dataclass
class ContentItemDto(ItemDto):
    id: str = ""
    externalid: str = ""
    title: str = ""
    description: str = ""
    longDescription: str = ""
    teaserimage: str = ""
    genreCategory: str = ""
    subgenreCategories: str = ""
    thematicCategories: str = ""
    showTitle: str = ""
    createdFormatted: str = ""
    crid: str = ""
    showId: str = ""
    duration: int = 0
    _viewer: str = ""

    @property
    def viewer(self) -> str:
        if self._position == constants.ITEM_POSITION_START:
            self._viewer = "ContentStartCard@view.cards.content_start_card"
        elif self._position == constants.ITEM_POSITION_RECO:
            self._viewer = "ContentRecoCard@view.cards.content_reco_card"
        else:
            raise TypeError("Unknown Item position [" + self._position + "]")
        return self._viewer
