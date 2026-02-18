import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logger():
    """Настройка логирования"""
    logger = logging.getLogger("api_service")
    logger.setLevel(logging.DEBUG)

    # Формат логов
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Логирование в файл (ошибки и таймауты)
    error_handler = RotatingFileHandler("error.log", maxBytes=10485760, backupCount=5)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # Логирование в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()
