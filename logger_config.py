import logging
from datetime import datetime
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"{datetime.now():%Y-%m-%d_%H-%M-%S}.txt"


def _build_logger():
    logger = logging.getLogger("keyword_extraction")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)

    return logger


logger = _build_logger()
logger.info("日志系统启动，日志文件：%s", LOG_FILE)
