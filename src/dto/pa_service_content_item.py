import constants
from dataclasses import dataclass
from dto.item import ItemDto
from datetime import datetime

@dataclass
class PaServiceContentItemDto(ItemDto):
    externalId: str = ''
    sophoraId: str = ''
    title: str = ''
    description: str = ''
    contentType: str = ''
    availableFrom: str = ''
    availableTo: str = ''
    firstPublicationDate: str = ''
    language: str = ''
    duration: int = 0
    structureNodePath: str = ''
    site: str = ''
    domain: str = ''
    teaserImageUrl: str = ''
    score: int = 0
    _viewer: str = ''

    @property
    def viewer(self) -> str:
        if self._position == constants.ITEM_POSITION_START:
            self._viewer = 'PaServiceContentStartCard@view.cards.paservice_cards.pa_service_content_start_card'
        elif self._position == constants.ITEM_POSITION_RECO:
            self._viewer = 'PaServiceContentRecoCard@view.cards.paservice_cards.pa_service_content_reco_card'
        else:
            raise TypeError('Unknown Item position [' + self._position + ']')
        return self._viewer