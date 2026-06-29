import sys
from pathlib import Path

from loguru import logger

_configured = False


def get_logger():
    global _configured
    if _configured:
        return logger

    logger.remove()
    fmt = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan> - <level>{message}</level>"
    )
    logger.add(sys.stderr, level="INFO", colorize=True, format=fmt)
    logger.add(
        Path("logs") / "embed_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        rotation="50 MB",
        retention="14 days",
        encoding="utf-8",
    )

    _configured = True
    return logger
