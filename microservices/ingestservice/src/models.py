from typing import Annotated
from pydantic import BaseModel, Field


class Shard(BaseModel):
    total: int
    successful: int
    failed: int


class OpenSearchResponse(BaseModel):
    index: Annotated[str, Field(alias="_index")]
    id: Annotated[str, Field(alias="_id")]
    version: Annotated[int, Field(alias="_version")]
    result: str
    shards: Annotated[Shard, Field(alias="_shards")]
    seq_no: Annotated[int, Field(alias="_seq_no")]
    primary_term: Annotated[int, Field(alias="_primary_term")]


class StorageChangeEvent(BaseModel):
    name: str
    bucket: str
