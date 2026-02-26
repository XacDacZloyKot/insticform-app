from typing import Callable, AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from src.db.uow import UnitOfWork
from src.core.settings import settings


class DatabaseConnection:
    """
        Управляет подключением к базе данных и созданием асинхронных сессий.
    """

    def __init__(self, db_url: str, db_echo: bool):
        """
            Инициализирует подключение к базе данных.
            Параметры пула (pool_size, max_overflow) удалены, так как SQLite их не поддерживает.
        """
        self.engine = create_async_engine(
            url=db_url,
            echo=db_echo,
            # Для SQLite можно добавить параметр check_same_thread=False в connect_args,
            # если возникнут проблемы с потоками
            connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
        )

        self.session_factory: Callable[[], AsyncSession] = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False
        )

    async def get_uow(self) -> AsyncGenerator[UnitOfWork, None]:
        # Фабрика возвращает асинхронную сессию
        session = self.session_factory()
        async with UnitOfWork(session) as uow:
            yield uow


# Создаем глобальный экземпляр подключения (Singleton) для переиспользования в приложении
db_connection = DatabaseConnection(
    db_url=settings.db.url,
    db_echo=settings.db.echo
)


# Эта функция будет использоваться в FastAPI Depends
async def get_uow_dependency() -> AsyncGenerator[UnitOfWork, None]:
    async for uow in db_connection.get_uow():
        yield uow