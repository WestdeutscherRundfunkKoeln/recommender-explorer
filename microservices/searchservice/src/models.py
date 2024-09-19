from pydantic import BaseModel


class CreateDocumentRequest(BaseModel, extra="allow"):
    id: str
