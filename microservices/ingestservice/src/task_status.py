from src.models import BulkIngestTask, BulkIngestTaskStatus
from datetime import datetime, timedelta, timezone


class TaskStatus:
    _tasks: dict[str, BulkIngestTask] = {}
    _lifetime_seconds = 60 * 60 * 24 * 7

    def __init__(self, id: str) -> None:
        self.id = id

    @classmethod
    def spawn(cls, id: str) -> "TaskStatus":
        task_status = cls(id)
        cls.put(
            id,
            BulkIngestTask(
                id=id,
                status=BulkIngestTaskStatus.PREPROCESSING,
                errors=[],
                created_at=datetime.now(tz=timezone.utc),
            ),
        )
        return task_status

    def set_status(self, status: BulkIngestTaskStatus) -> None:
        self._tasks[self.id].status = status
        if status == BulkIngestTaskStatus.COMPLETED:
            self._tasks[self.id].completed_at = datetime.now(tz=timezone.utc)

    def add_error(self, error: str) -> None:
        self._tasks[self.id].errors.append(error)

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
