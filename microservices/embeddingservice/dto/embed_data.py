from pydantic import BaseModel
from typing import Optional


class EmbedData(BaseModel):
    id: Optional[str] = ""
    embedText: str