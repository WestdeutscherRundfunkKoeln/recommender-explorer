import logging

from src.task_status import TaskStatus
from src.log_handler import TaskLogHandler


def test_task_handler():
    with TaskStatus("test") as task:
        handler = TaskLogHandler()
        logger = logging.getLogger("test")
        logger.addHandler(handler)

        logger.error("test error", extra={"task": task})

        data = task.get("test")

    assert data is not None
    assert data.errors == ["test error"]
