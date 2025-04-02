import logging

from src.task_status import TaskStatus


class TaskLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno != logging.ERROR:
            return

        task: TaskStatus | None = getattr(record, "task", None)
        if task is None:
            return

        task.add_error(self.format(record))
