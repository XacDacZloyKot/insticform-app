from typing import Dict, Type, Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger("UnitOfWork")

class UnitOfWork:
    """
    Unit of Work для управления транзакциями и репозиториями.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._repositories: Dict[Type, Any] = {}

    def get_repository(self, repo_class: Type):
        if repo_class not in self._repositories:
            self._repositories[repo_class] = repo_class(self.session)
        return self._repositories[repo_class]

    async def commit(self):
        """Зафиксировать все изменения в транзакции"""
        try:
            await self.session.commit()
            logger.debug("Транзакция успешно зафиксирована")
        except Exception as e:
            logger.error(f"Ошибка при коммите транзакции: {str(e)}")
            await self.rollback()
            raise

    async def rollback(self):
        """Откатить текущую транзакцию"""
        try:
            await self.session.rollback()
            logger.debug("Транзакция откачена")
        except Exception as e:
            logger.error(f"Ошибка при откате транзакции: {str(e)}")
            raise

    async def close(self):
        """Закрыть сессию"""
        await self.session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.warning(f"Обнаружена ошибка в UOW: {exc_type.__name__}: {exc_val}")
            await self.rollback()
        else:
            await self.commit()
        await self.close()