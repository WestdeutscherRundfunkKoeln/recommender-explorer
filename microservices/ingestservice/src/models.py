from typing import Annotated, Iterable
from pydantic import BaseModel, Field
import enum
import datetime


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

    @property
    def blob_id(self):
        return self.name.split("/")[-1].split(".")[0]


class FullLoadRequest(BaseModel):
    bucket: str
    prefix: str


class FullLoadResponse(BaseModel):
    task_id: str


class BulkIngestTaskStatus(str, enum.Enum):
    PREPROCESSING = "PREPROCESSING"
    IN_FLIGHT = "IN_FLIGHT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BulkIngestTask(BaseModel):
    id: str
    status: BulkIngestTaskStatus
    errors: list[str]
    created_at: datetime.datetime
    completed_at: datetime.datetime | None = None


class SingleTaskResponse(BaseModel):
    task: BulkIngestTask | None


class TasksResponse(BaseModel):
    tasks: Iterable[BulkIngestTask]
