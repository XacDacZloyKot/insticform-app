import logging

from src.core.settings import settings


def setup_logging():
    """
        Настраивает логирование для приложения.

        Использует настройки из конфигурации (settings.logger) для установки уровня логирования,
        формата вывода и обработчиков (handlers).
    """
    logging.basicConfig(
        level=settings.logger.log_level,
        format=settings.logger.format,
        handlers=[
            logging.StreamHandler(),
        ]
    )

    logger = logging.getLogger("System")
    logger.info("Настройки логирования успешно применены.")
