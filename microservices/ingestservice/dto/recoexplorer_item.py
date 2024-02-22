from typing import Optional
from pydantic import BaseModel, Extra, ConfigDict, field_serializer
from datetime import datetime


class RecoExplorerItem(BaseModel, extra=Extra.allow):
    externalid: str
    id: str
    title: str
    description: str
    longDescription: str
    availableFrom: datetime
    availableTo: datetime
    duration: Optional[int] = -1
    thematicCategories: list
    thematicCategoriesIds: Optional[list] = []
    thematicCategoriesTitle: Optional[list] = []
    genreCategory: str
    genreCategoryId: Optional[str] = ""
    subgenreCategories: list
    subgenreCategoriesIds: Optional[list] = []
    subgenreCategoriesTitle: Optional[list] = []
    teaserimage: str
    geoAvailability: Optional[str] = ""
    embedText: Optional[str] = ""
    embedTextHash: Optional[str] = ""
    episodeNumber: Optional[str] = ""
    hasAudioDescription: Optional[bool] = False
    hasDefaultVersion: Optional[bool] = False
    hasSignLanguage: Optional[bool] = False
    hasSubtitles: Optional[bool] = False
    isChildContent: Optional[bool] = False
    isOnlineOnly: Optional[bool] = False
    isOriginalLanguage: Optional[bool] = False
    producer: Optional[str] = ""
    publisherId: Optional[str] = ""
    seasonNumber: Optional[str] = ""
    sections: Optional[str] = ""
    showCrid: Optional[str] = ""
    showId: Optional[str] = ""
    showTitel: Optional[str] = ""  # showTitle?
    showType: Optional[str] = ""

    @field_serializer("availableFrom")
    def serialize_dt(self, dt: datetime, _info):
        return dt.timestamp()

    @field_serializer("availableTo")
    def serialize_dt(self, dt: datetime, _info):
        return dt.timestamp()

    @property
    def extra_fields(
        self,
    ) -> set[str]:  # accept extra fields from client which are not defined in class
        return set(self.__dict__) - set(self.__fields__)
