"""
Logging configuration with daily rotating log files (log-YYYY-MM-DD.log).
"""

import logging
from datetime import datetime
from io import TextIOWrapper
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional, cast

from api.config.settings import settings


class DailyRotatingFileHandler(TimedRotatingFileHandler):
    """
    Custom handler that creates daily log files with format log-YYYY-MM-DD.log.
    """

    def __init__(
        self,
        log_dir: str = "logs",
        *,
        backup_count: Optional[int] = None,
        encoding: str = "utf-8",
    ):
        backup_count = backup_count or settings.LOG_RETENTION_DAYS
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        today = datetime.now().strftime("%Y-%m-%d")
        filename = self.log_dir / f"log-{today}.log"

        super().__init__(
            filename=str(filename),
            when="midnight",
            interval=1,
            backupCount=backup_count,
            encoding=encoding,
        )

    def doRollover(self) -> None:  # noqa: N802
        if self.stream:
            self.stream.close()
            self.stream = cast(TextIOWrapper, None)

        today = datetime.now().strftime("%Y-%m-%d")
        self.baseFilename = str(self.log_dir / f"log-{today}.log")

        if not self.delay:
            self.stream = self._open()

    def getFilesToDelete(self) -> list[str]:  # noqa: N802
        dir_path = Path(self.baseFilename).parent
        result = sorted(str(file_name) for file_name in dir_path.glob("log-*.log"))

        if len(result) > self.backupCount:
            return result[: len(result) - self.backupCount]
        return []


def setup_logging() -> None:
    """
    Setup logging with console output and daily rotating file handler.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    file_handler = DailyRotatingFileHandler(
        backup_count=settings.LOG_RETENTION_DAYS, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        (
            "%(asctime)s - %(name)s - %(levelname)s - %(module)s - "
            "%(funcName)s - %(lineno)d - %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        setup_logging()
    return logging.getLogger(name)
