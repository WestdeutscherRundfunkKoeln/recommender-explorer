from pydantic import BaseModel


class EmbeddingRequest(BaseModel):
    embedText: str
    models: list[str] | None = None
    returnEmbedText: bool = False


class AddEmbeddingToDocRequest(BaseModel):
    id: str
    embedText: str
    models: list[str] | None = None
