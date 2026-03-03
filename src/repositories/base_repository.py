import logging
from typing import Optional, List, Union, Dict, Any

from pydantic import BaseModel
from sqlalchemy import select, desc, asc, delete, func
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Generic, TypeVar

from src.model.domain.base import Base
from src.repositories.decorators import with_exception_handling, with_read_operation_handling

logger = logging.getLogger("BaseRepository")

ModelType = TypeVar(name="ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Базовый репозиторий для работы с моделями базы данных.
    Реализует основные CRUD-операции (создание, чтение, обновление, удаление).
    """

    def __init__(self, session: AsyncSession, model: type(ModelType)):
        self._session = session
        self.model: type[ModelType] = model
        self.model_name = model.__name__

    @with_read_operation_handling("Ошибка при получении списка")
    async def list(
            self,
            order_by: Optional[str] = None,
            order_direction: Optional[str] = "asc",
            offset: Optional[int] = None,
            limit: Optional[int] = None,
            **filters
    ) -> List[ModelType]:
        query = select(self.model)

        if filters:
            query = query.filter_by(**filters)

        if order_by:
            column = getattr(self.model, order_by, None)
            if not column:
                logger.error(f"Ошибка сортировки в list методе для {self.model_name}: {order_by}")
                raise ValueError(f"Неверное поле order_by: {order_by}")

            if order_direction == "asc":
                query = query.order_by(asc(column))
            elif order_direction == "desc":
                query = query.order_by(desc(column))
            else:
                logger.error(f"Ошибка сортировки в list методе для {self.model_name}: {order_by}")
                raise ValueError(f"Неверное направление сортировки(order_direction): {order_direction}")

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        stmt = await self._session.execute(query)
        result = stmt.scalars().all()

        logger.debug(f"Метод list успешно выполнен для модели: {self.model_name}")
        return result

    @with_read_operation_handling("Ошибка при получении списка с подгрузкой связей")
    async def list_with_joins(
            self,
            joins: Optional[List] = None,
            order_by: Optional[str] = None,
            order_direction: Optional[str] = "asc",
            offset: Optional[int] = None,
            limit: Optional[int] = None,
            **filters
    ) -> List[ModelType]:
        query = select(self.model)

        if joins:
            for join in joins:
                query = query.options(join)

        if filters:
            query = query.filter_by(**filters)

        if order_by:
            column = getattr(self.model, order_by, None)
            if not column:
                logger.error(f"Ошибка сортировки в list_with_joins методе для {self.model_name}: {order_by}")
                raise ValueError(f"Неверное поле order_by: {order_by}")

            if order_direction == "asc":
                query = query.order_by(asc(column))
            elif order_direction == "desc":
                query = query.order_by(desc(column))
            else:
                logger.error(f"Ошибка сортировки в list_with_joins методе для {self.model_name}: {order_direction}")
                raise ValueError(f"Неверное направление сортировки(order_direction): {order_direction}")

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        stmt = await self._session.execute(query)
        result = stmt.unique().scalars().all()

        logger.debug(f"Метод list_with_joins успешно выполнен для модели: {self.model_name}")
        return result

    @with_read_operation_handling("Ошибка при поиске первого элемента")
    async def find_first(self, **filters) -> Optional[ModelType]:
        query = select(self.model).filter_by(**filters).limit(1)
        result = await self._session.execute(query)
        entity = result.scalar_one_or_none()

        logger.debug(f"Find first выполнен для {self.model_name}, найдено: {entity is not None}")
        return entity

    @with_read_operation_handling("Ошибка при поиске первого элемента с подгрузкой связей")
    async def find_first_with_joins(self, joins: Optional[List] = None, **filters) -> Optional[ModelType]:
        query = select(self.model).filter_by(**filters).limit(1)

        if joins:
            for join in joins:
                query = query.options(join)

        result = await self._session.execute(query)
        entity = result.scalar_one_or_none()

        logger.debug(f"Find first with joins выполнен для {self.model_name}, найдено: {entity is not None}")
        return entity

    @with_read_operation_handling("Ошибка при получении одного элемента")
    async def get_one(self, **filters) -> ModelType:
        try:
            query = select(self.model).filter_by(**filters)
            result = await self._session.scalars(query)
            entity = result.one()

            logger.debug(f"Get one метод успешно выполнен для {self.model_name} с фильтрами: {filters}")
            return entity
        except NoResultFound as e:
            filters_str = self._format_filters(filters)
            logger.error(f"Объект {self.model_name} с параметрами {filters_str} не найден")
            raise NoResultFound(f"Объект {self.model_name} с параметрами {filters_str} не найден") from e
        except MultipleResultsFound as e:
            filters_str = self._format_filters(filters)
            logger.error(f"Найдено несколько объектов {self.model_name} с фильтрами: {filters_str}")
            raise MultipleResultsFound(f"Найдено несколько объектов {self.model_name} с фильтрами: {filters_str}") from e

    @with_read_operation_handling("Ошибка при получении одного элемента с подгрузкой связей")
    async def get_one_with_joins(self, joins: Optional[List] = None, **filters) -> ModelType:
        try:
            query = select(self.model).filter_by(**filters)

            if joins:
                for join in joins:
                    query = query.options(join)

            result = await self._session.scalars(query)
            entity = result.one()

            logger.debug(f"Get one with joins метод успешно выполнен для {self.model_name} с фильтрами: {filters}")
            return entity
        except NoResultFound as e:
            filters_str = self._format_filters(filters)
            logger.error(f"Объект {self.model_name} с параметрами {filters_str} не найден")
            raise NoResultFound(f"Объект {self.model_name} с параметрами {filters_str} не найден") from e
        except MultipleResultsFound as e:
            filters_str = self._format_filters(filters)
            logger.error(f"Найдено несколько объектов {self.model_name} с фильтрами: {filters_str}")
            raise MultipleResultsFound(f"Найдено несколько объектов {self.model_name} с фильтрами: {filters_str}") from e

    @with_exception_handling("Ошибка при создании")
    async def create(self, data: ModelType) -> ModelType:
        self._session.add(data)
        await self._session.flush()
        await self._session.refresh(data)
        logger.info(f"Метод создания выполнен успешно для {self.model_name}, data: {data}")
        return data

    @with_exception_handling("Ошибка при удалении")
    async def delete(self, id: int) -> None:
        entity = await self._session.get(self.model, id)

        if not entity:
            logger.error(f"Ошибка: не найдена запись {self.model_name} в методе delete: id {id}")
            raise ValueError(f"{self.model_name} с id {id} не найдена")

        await self._session.delete(entity)
        logger.info(f"Объект {self.model_name} с id {id} помечен для удаления")

    @with_exception_handling("Ошибка при обновлении")
    async def update(self, id: int, data: Union[BaseModel, Dict[str, Any]]) -> ModelType:
        entity = await self._session.get(self.model, id)

        if not entity:
            logger.warning(f"Модель {self.model_name} с ID '{id}' не найдена")
            raise ValueError(f"Модель {self.model_name} с ID '{id}' не найдена")

        update_data = data.model_dump(exclude_unset=True) if isinstance(data, BaseModel) else data
        update_data.pop('id', None)

        updated_fields = []
        for field, value in update_data.items():
            if hasattr(entity, field):
                setattr(entity, field, value)
                updated_fields.append(field)
            else:
                logger.warning(f"Поле {field} не найдено в модели {self.model_name}")

        await self._session.flush()
        await self._session.refresh(entity)

        logger.info(f"Обновлен объект {self.model_name} с ID: {id}, измененные поля: {updated_fields}")
        return entity

    @with_exception_handling("Ошибка при массовом удалении")
    async def delete_many(self, ids: List[int]) -> int:
        if not ids:
            return 0

        stmt = delete(self.model).where(self.model.id.in_(ids))
        result = await self._session.execute(stmt)

        deleted_count = result.rowcount
        logger.info(f"Помечено для удаления {deleted_count} объектов {self.model_name}")
        return deleted_count

    @with_read_operation_handling("Ошибка при подсчете записей")
    async def count(self, filters: Optional[Dict] = None) -> int:
        query = select(func.count()).select_from(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        result = await self._session.execute(query)
        return result.scalar_one()

    @staticmethod
    def _format_filters(filters: dict) -> str:
        return ", ".join([f"{k}={v}" for k, v in filters.items()])