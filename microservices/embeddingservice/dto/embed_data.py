from pydantic import BaseModel


class EmbeddingRequest(BaseModel):
    embedText: str
    models: list[str] | None = None


class AddEmbeddingToDocRequest(BaseModel):
    id: str
    embedText: str
    models: list[str] | None = None
