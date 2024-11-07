import logging

from src.task_status import TaskStatus


class TaskLogHandler(logging.Handler):
    def __init__(self, task: TaskStatus) -> None:
        super().__init__()
        self._task = task

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno == logging.ERROR:
            self._task.add_error(self.format(record))
