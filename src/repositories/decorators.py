import logging
from functools import wraps
from typing import Callable, Any

from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("RepositoryExceptionHandlers")


def with_exception_handling(error_message: str = "Ошибка базы данных") -> Callable:
    """
    Декоратор для обработки исключений в репозиториях.
    Только логирует и преобразует исключения.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            try:
                return await func(self, *args, **kwargs)
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemyError в {func.__name__} для {self.model_name}: {str(e)}")
                raise SQLAlchemyError(f"{error_message}: {str(e)}")
            except Exception as e:
                logger.error(f"Неожиданная ошибка в {func.__name__} для {self.model_name}: {str(e)}")
                raise RuntimeError(f"Неожиданная ошибка: {str(e)}")
        return wrapper
    return decorator


def with_read_operation_handling(error_message: str = "Ошибка при чтении данных") -> Callable:
    """
    Специализированный декоратор для операций чтения.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> Any:
            try:
                return await func(self, *args, **kwargs)
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemyError при чтении в {func.__name__} для {self.model_name}: {str(e)}")
                raise SQLAlchemyError(f"{error_message}: {str(e)}")
            except Exception as e:
                logger.error(f"Неожиданная ошибка при чтении в {func.__name__} для {self.model_name}: {str(e)}")
                raise RuntimeError(f"Ошибка при чтении данных: {str(e)}")
        return wrapper
    return decorator