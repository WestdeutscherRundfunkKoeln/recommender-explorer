from pydantic import BaseModel


class CreateDocumentRequest(BaseModel):
    id: str
    data: dict
