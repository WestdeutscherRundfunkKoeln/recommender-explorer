from pydantic import BaseModel
from typing import Optional


class EmbedData(BaseModel):
    id: Optional[str] = ""
    models: Optional[list[str]] = None
    embedText: str