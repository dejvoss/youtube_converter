from __future__ import annotations

import logging
from pathlib import Path


def setup_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("konwerter_mp3")
    logger.setLevel(logging.DEBUG)
    # Avoid duplicate handlers if re-initialised
    for h in list(logger.handlers):
        logger.removeHandler(h)
    handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    )
    logger.addHandler(handler)
    logger.propagate = False
    return logger
