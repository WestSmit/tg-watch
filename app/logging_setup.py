import logging


def configure_logging(log_level: str) -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s %(levelname)s [tgwatch] %(message)s",
    )
    return logging.getLogger("tgwatch")
