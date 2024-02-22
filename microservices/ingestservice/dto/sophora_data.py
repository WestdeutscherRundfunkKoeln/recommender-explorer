from pydantic import BaseModel
from datetime import datetime
from microservices.ingestservice.dto.media_data import MediaData

class SophoraData(MediaData):
    # externalId: str
    uuid: str
    sophoraId: str
    type: str
    typeDef: list
    title: str
    description: str
    longDescription: str
    availableFrom: datetime
    availableTo: datetime
    firstPublicationDate: datetime
    keywords: list
    language: str
    durationSeconds: int
    thematicCategories: list
    genreCategory: str | None = None
    subgenreCategories: list = None
    filterCategory: list
    structurePath: str
    site: str
    domain: str
    teaserImage: dict
    fskAgeRating: str
    contentRatings: str
    geoAvailability: str

