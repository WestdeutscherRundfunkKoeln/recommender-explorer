from typing import Optional
from pydantic import BaseModel, Extra
from datetime import datetime


class RecoExplorerItem(BaseModel, extra=Extra.allow):
    externalid: str
    id: Optional[str] = ''
    title: str
    description: str
    longDescription: str
    availableFrom: str
    availableTo: str
    duration: Optional[int] = None
    thematicCategories: list
    thematicCategoriesIds: Optional[list] = []
    thematicCategoriesTitle: Optional[list] = []
    genreCategory: str
    genreCategoryId: Optional[str] = ''
    subgenreCategories: list
    subgenreCategoriesIds: Optional[list] = []
    subgenreCategoriesTitle: Optional[list] = []
    teaserimage: str
    geoAvailability: Optional[str] = ''
    embedText: Optional[str] = ''
    embedTextHash: Optional[str] = ''
    episodeNumber: Optional[str] = ''
    hasAudioDescription: Optional[bool] = None
    hasDefaultVersion: Optional[bool] = None
    hasSignLanguage: Optional[bool] = None
    hasSubtitles: Optional[bool] = None
    isChildContent: Optional[bool] = None
    isOnlineOnly: Optional[bool] = None
    isOriginalLanguage: Optional[bool] = None
    producer: Optional[str] = ''
    publisherId: Optional[str] = ''
    seasonNumber: Optional[str] = ''
    sections: Optional[str] = ''
    showCrid: Optional[str] = ''
    showId: Optional[str] = ''
    showTitel: Optional[str] = '' # showTitle?
    showType: Optional[str] = ''
    startDate: Optional[datetime] = None

    @property
    def extra_fields(self) -> set[str]: # accept extra fields from client which are not defined in class
        return set(self.__dict__) - set(self.__fields__)
