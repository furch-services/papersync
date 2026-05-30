import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file: str = "/app/logs/app.log") -> logging.Logger:
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("papersync")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10_000_000, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger
