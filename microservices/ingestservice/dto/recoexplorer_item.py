from typing import Optional
from pydantic import BaseModel, field_serializer
from datetime import datetime


class RecoExplorerItem(BaseModel, extra="allow"):
    externalid: str
    id: str
    cmsId: str
    title: str
    description: str
    longDescription: str
    availableFrom: datetime
    availableTo: datetime
    duration: Optional[int] = -1
    thematicCategories: list
    thematicCategoriesIds: Optional[list] = []
    thematicCategoriesTitle: Optional[list] = []
    genreCategory: Optional[str] = ""
    genreCategoryId: Optional[str] = ""
    subgenreCategories: list
    subgenreCategoriesIds: Optional[list] = []
    subgenreCategoriesTitle: Optional[list] = []
    teaserimage: str
    geoAvailability: Optional[str] = ""
    embedText: str
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
    needs_reembedding: Optional[bool] = True

    @field_serializer("availableFrom", "availableTo")
    def serialize_dt(self, dt: datetime, _info):
        return dt.strftime("%Y-%m-%dT%H:%M:%S%z")

    @property
    def extra_fields(
        self,
    ) -> set[str]:  # accept extra fields from client which are not defined in class
        return set(self.__dict__) - set(self.__fields__)
