from pydantic import BaseModel


class EmbeddingRequest(BaseModel):
    embedText: str
    models: list[str] | None = None
    return_embed_text = False


class AddEmbeddingToDocRequest(BaseModel):
    id: str
    embedText: str
    models: list[str] | None = None
