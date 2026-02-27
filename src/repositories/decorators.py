import logging
from functools import wraps
from typing import Callable, Any

from sqlalchemy.exc import SQLAlchemyError
from src.repositories.base_repository.exceptions import ExceptionBase, MultipleResultsFoundException, NotFoundException

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
            except (NotFoundException, MultipleResultsFoundException):
                raise
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemyError в {func.__name__} для {self.model_name}: {str(e)}")
                raise SQLAlchemyError(f"{error_message}: {str(e)}")
            except Exception as e:
                logger.error(f"Неожиданная ошибка в {func.__name__} для {self.model_name}: {str(e)}")
                raise ExceptionBase(detail=f"Неожиданная ошибка: {str(e)}", status=500)
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
            except (NotFoundException, MultipleResultsFoundException):
                raise
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemyError при чтении в {func.__name__} для {self.model_name}: {str(e)}")
                raise SQLAlchemyError(f"{error_message}: {str(e)}")
            except Exception as e:
                logger.error(f"Неожиданная ошибка при чтении в {func.__name__} для {self.model_name}: {str(e)}")
                raise ExceptionBase(detail=f"Ошибка при чтении данных: {str(e)}", status=500)
        return wrapper
    return decorator