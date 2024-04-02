from pydantic import BaseModel


class EmbedData(BaseModel):
    id: str
    embedText: str