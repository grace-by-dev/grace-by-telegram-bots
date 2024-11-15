import logging


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler("bot.log")
    handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | (%(levelname)s): %(message)s (Line:" + "%(lineno)d) [%(filename)s]",
        datefmt="%d-%m-%Y %I:%M:%S",
    )

    handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.addHandler(console_handler)

    return logger
