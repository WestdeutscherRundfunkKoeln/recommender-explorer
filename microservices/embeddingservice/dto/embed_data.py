from typing import Optional

from pydantic import BaseModel


class EmbedData(BaseModel):
    id: Optional[str] = ""
    embedText: str
