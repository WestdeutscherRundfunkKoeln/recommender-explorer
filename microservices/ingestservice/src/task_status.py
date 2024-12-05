import json
import logging
from datetime import datetime, timedelta, timezone
from types import TracebackType
from typing import cast

from google.cloud.exceptions import GoogleCloudError
from google.cloud.storage import Bucket

from src.models import BulkIngestTask, BulkIngestTaskStatus

logger = logging.getLogger(__name__)


class TaskStatus:
    _tasks: dict[str, BulkIngestTask] = {}
    _lifetime_seconds = 60 * 60 * 24 * 7  # 1 week

    def __init__(self, id: str, log_bucket: Bucket) -> None:
        self.id = id
        self.log_bucket = log_bucket

    def set_status(self, status: BulkIngestTaskStatus) -> None:
        self._tasks[self.id].status = status
        if status == BulkIngestTaskStatus.COMPLETED:
            self._tasks[self.id].completed_at = datetime.now(tz=timezone.utc)

    def add_error(self, error: str) -> None:
        self._tasks[self.id].errors.append(error)

    def increment_completed(self, value: int = 1) -> None:
        self._tasks[self.id].completed_items += value

    def increment_failed(self, value: int = 1) -> None:
        self._tasks[self.id].failed_items += value

    def __enter__(self) -> "TaskStatus":
        logger.info("Starting ingest task %s", self.id)
        self.put(
            self.id,
            BulkIngestTask(
                id=self.id,
                status=BulkIngestTaskStatus.PREPROCESSING,
                errors=[],
                created_at=datetime.now(tz=timezone.utc),
            ),
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        result = (
            self._on_success()
            if exc_type is None
            else self._on_error(exc_type, exc_val, exc_tb)
        )
        try:
            self.log_bucket.blob(f"{self.id}.json").upload_from_string(
                cast(BulkIngestTask, self.get(self.id)).model_dump_json()
            )
        except GoogleCloudError:
            logger.error("Error during upload of log file", exc_info=True)
        return result

    def _on_success(self) -> None:
        logger.info("Ingest task %s completed", self.id)
        self.set_status(BulkIngestTaskStatus.COMPLETED)

    def _on_error(
        self,
        exc_type: type[BaseException],
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        assert exc_val is not None
        assert exc_tb is not None
        logger.error(
            "Error during ingest task %s",
            self.id,
            exc_info=(exc_type, exc_val, exc_tb),
        )
        self.add_error(str(exc_val))
        self.set_status(BulkIngestTaskStatus.FAILED)
        return True

    @classmethod
    def get(cls, id: str) -> BulkIngestTask | None:
        return cls._tasks.get(id)

    @classmethod
    def put(cls, id: str, task: BulkIngestTask) -> None:
        cls._tasks[id] = task

    @classmethod
    def get_tasks(cls) -> dict[str, BulkIngestTask]:
        return cls._tasks

    @classmethod
    def clear(cls) -> None:
        now = datetime.now(tz=timezone.utc)
        for task in list(cls._tasks.values()):
            if (now - task.created_at) > timedelta(seconds=cls._lifetime_seconds):
                del cls._tasks[task.id]
