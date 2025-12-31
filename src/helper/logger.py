import logging


def create_logger(
    name: str,
    *,
    level: int = logging.INFO,
    format: str = '%(asctime)s | %(name)s | %(levelname)s | %(message)s',  # noqa: A002
    datefmt: str | None = None,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if function is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)

        formatter = logging.Formatter(fmt=format, datefmt=datefmt)
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    logger.propagate = False
    return logger
