from pydantic import BaseModel
from datetime import datetime


class MediaData(BaseModel):
    externalId: str
