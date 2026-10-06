"""Application logging configuration."""

import logging as standard_logging
from pathlib import Path

from app.core.config import settings

LOG_DIRECTORY = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE = LOG_DIRECTORY / "app.log"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_CONFIGURED_ATTRIBUTE = "_ai_knowledge_chatbot_logging_configured"


def configure_logging() -> None:
    """Configure console and file handlers once for the application process."""

    root_logger = standard_logging.getLogger()
    if getattr(root_logger, _CONFIGURED_ATTRIBUTE, False):
        return

    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

    level = standard_logging.DEBUG if settings.debug else standard_logging.INFO
    formatter = standard_logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )

    console_handler = standard_logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = standard_logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    # HTTP/2 header-decoding traces are extremely noisy when application
    # DEBUG is enabled and do not help diagnose user requests.
    for logger_name in ("httpcore", "httpx", "httpx2", "hpack", "urllib3"):
        standard_logging.getLogger(logger_name).setLevel(standard_logging.INFO)
    setattr(root_logger, _CONFIGURED_ATTRIBUTE, True)
