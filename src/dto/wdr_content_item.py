import constants
from dataclasses import dataclass
from dto.item import ItemDto


@dataclass
class WDRContentItemDto(ItemDto):
    availableFrom: str = ''
    availableTo: str = ''
    contentRatings: str = ''
    description: str = ''
    domain: str = ''
    duration: int = 0
    embedText: str = ''
    embedTextHash: str = ''
    episodeNumber: str = ''
    externalid: str = ''
    firstPublicationDate: str = ''
    fskAgeRating: str = ''
    geoAvailability: str = ''
    genreCategoryId: str = ''
    hasAudioDescription: 'bool' = False
    hasDefaultVersion: bool = False
    hasSignLanguage: bool = False
    hasSubtitles: bool = False
    id: str = ''
    isChildContent: bool = False
    isOnlineOnly: bool = False
    keywords: str = ''
    language: str = ''
    longDescription: str = ''
    producer: str = ''
    publisherId: str = ''
    sections: str = ''
    seasonNumber: str = ''
    showCrid: str = ''
    showId: str = ''
    showTitel: str = ''
    showType: str = ''
    site: str = ''
    cmsId: str = ''
    structurePath: str = ''
    teaserimage: str = ''
    thematicCategories: str = ''
    title: str = ''
    type: str = ''
    uuid: str = ''
    _viewer: str = ''

    @property
    def viewer(self) -> str:
        match self._position:
            case constants.ITEM_POSITION_START:
                self._viewer = 'WDRContentStartCard@view.cards.wdr.wdr_content_start_card'
            case constants.ITEM_POSITION_RECO:
                self._viewer = 'WDRContentRecoCard@view.cards.wdr.wdr_content_reco_card'
            case _:
                raise TypeError('Unknown Item position [' + self._position + ']')
        return self._viewer
