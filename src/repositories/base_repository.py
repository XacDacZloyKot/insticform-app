import logging
from typing import Optional, List, Union, Dict, Any

from pydantic import BaseModel
from sqlalchemy import select, desc, asc, delete, func
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from typing_extensions import Generic, TypeVar

from src.model.domain.base import Base
from src.repositories.decorators import with_exception_handling, with_read_operation_handling
from src.repositories.base_repository.exceptions import MultipleResultsFoundException, NotFoundException

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
        """
        Возвращает список объектов модели с возможностью сортировки, пагинации и фильтрации.

        :param order_by: Поле, по которому выполняется сортировка. Если не указано, сортировка не применяется.
        :param order_direction: Направление сортировки (`asc` для возрастания, `desc` для убывания). По умолчанию `asc`.
        :param offset: Смещение для пагинации. Если не указано, пагинация не применяется.
        :param limit: Лимит для пагинации. Если не указано, пагинация не применяется.

        :raises SQLAlchemyError: Если произошла ошибка базы данных.
        :raises ValueError: Если поле order_by или order_direction указано не правильно.
        :raises ExceptionBase: Если возникла неожиданная ошибка.
        """
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
        """
        Возвращает список объектов модели с подгрузкой связей.

        :param joins: Список связей для подгрузки (joinedload, selectinload)
        :param order_by: Поле, по которому выполняется сортировка
        :param order_direction: Направление сортировки (`asc` для возрастания, `desc` для убывания)
        :param offset: Смещение для пагинации
        :param limit: Лимит для пагинации
        :param filters: Фильтры для запроса
        :return: Список объектов модели с подгруженными связями
        """
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
        """
        Возвращает первый объект модели, соответствующий указанным фильтрам.
        Использует метод list с ограничением в 1 результат для оптимизации запроса.

        :param filters: Параметры фильтрации в виде ключевых аргументов.
        :return: Первый найденный объект модели или None, если объекты не найдены.
        :raises SQLAlchemyError: Если произошла ошибка базы данных.
        :raises ExceptionBase: Если возникла неожиданная ошибка.
        """
        query = select(self.model).filter_by(**filters).limit(1)
        result = await self._session.execute(query)
        entity = result.scalar_one_or_none()

        logger.debug(f"Find first выполнен для {self.model_name}, найдено: {entity is not None}")
        return entity

    @with_read_operation_handling("Ошибка при поиске первого элемента с подгрузкой связей")
    async def find_first_with_joins(self, joins: Optional[List] = None, **filters) -> Optional[ModelType]:
        """
        Возвращает первый объект модели с подгрузкой связей.

        :param joins: Список связей для подгрузки (joinedload, selectinload)
        :param filters: Параметры фильтрации в виде ключевых аргументов.
        :return: Первый найденный объект модели с подгруженными связями или None
        """
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
        """
        Возвращает один объект модели, соответствующий указанным фильтрам.

        :param filters: Параметры фильтрации в виде ключевых аргументов.
        :return: Один объект модели.
        :raises NotFoundException: Если объект не найден.
        :raises MultipleResultsFoundException: Если найдено несколько объектов.
        :raises SQLAlchemyError: Если произошла ошибка базы данных.
        :raises ExceptionBase: Если возникла неожиданная ошибка.
        """
        try:
            query = select(self.model).filter_by(**filters)
            result = await self._session.scalars(query)
            entity = result.one()

            logger.debug(f"Get one метод успешно выполнен для {self.model_name} с фильтрами: {filters}")
            return entity
        except NoResultFound:
            filters_str = self._format_filters(filters)
            logger.error(f"Объект {self.model_name} с параметрами {filters_str} не найден")
            raise NotFoundException(
                error_message=f"с параметрами {filters_str}",
                class_name=self.model_name
            )
        except MultipleResultsFound:
            filters_str = self._format_filters(filters)
            logger.error(f"Найдено несколько объектов {self.model_name} с фильтрами: {filters_str}")
            raise MultipleResultsFoundException(
                error_message=f"параметры {filters_str}",
                class_name=self.model_name
            )

    @with_read_operation_handling("Ошибка при получении одного элемента с подгрузкой связей")
    async def get_one_with_joins(self, joins: Optional[List] = None, **filters) -> ModelType:
        """
        Возвращает один объект модели с подгрузкой связей.

        :param joins: Список связей для подгрузки (joinedload, selectinload)
        :param filters: Параметры фильтрации в виде ключевых аргументов.
        :return: Один объект модели с подгруженными связями.
        :raises NotFoundException: Если объект не найден.
        :raises MultipleResultsFoundException: Если найдено несколько объектов.
        """
        try:
            query = select(self.model).filter_by(**filters)

            if joins:
                for join in joins:
                    query = query.options(join)

            result = await self._session.scalars(query)
            entity = result.one()

            logger.debug(f"Get one with joins метод успешно выполнен для {self.model_name} с фильтрами: {filters}")
            return entity
        except NoResultFound:
            filters_str = self._format_filters(filters)
            logger.error(f"Объект {self.model_name} с параметрами {filters_str} не найден")
            raise NotFoundException(
                error_message=f"с параметрами {filters_str}",
                class_name=self.model_name
            )
        except MultipleResultsFound:
            filters_str = self._format_filters(filters)
            logger.error(f"Найдено несколько объектов {self.model_name} с фильтрами: {filters_str}")
            raise MultipleResultsFoundException(
                error_message=f"параметры {filters_str}",
                class_name=self.model_name
            )

    @with_exception_handling("Ошибка при создании")
    async def create(self, data: ModelType) -> ModelType:
        """
        Создает новый объект модели в базе данных.

        :param data: Объект модели для создания.

        :raises SQLAlchemyError: Если произошла ошибка базы данных.
        :raises ExceptionBase: Если возникла неожиданная ошибка.
        """
        self._session.add(data)
        await self._session.flush()
        await self._session.refresh(data)
        logger.info(f"Метод создания выполнен успешно для {self.model_name}, data: {data}")
        return data

    @with_exception_handling("Ошибка при удалении")
    async def delete(self, id: int) -> None:
        """
        Удаляет объект модели по его идентификатору.

        :param id: Идентификатор объекта для удаления.

        :raises NotFoundException: Если объект с указанным идентификатором не найден.
        :raises SQLAlchemyError: Если произошла ошибка базы данных.
        :raises ExceptionBase: Если возникла неожиданная ошибка.
        """
        entity = await self._session.get(self.model, id)

        if not entity:
            logger.error(f"Ошибка: не найдена запись {self.model_name} в методе delete: id {id}")
            raise NotFoundException(
                error_message=f"{self.model_name} с id {id} не найдена",
                class_name=self.model_name
            )

        await self._session.delete(entity)
        logger.info(f"Объект {self.model_name} с id {id} помечен для удаления")

    @with_exception_handling("Ошибка при обновлении")
    async def update(self, id: int, data: Union[BaseModel, Dict[str, Any]]) -> ModelType:
        """
        Обновляет запись в таблице.

        :param id: Идентификатор модели для обновления.
        :param data: Данные для обновления.

        :raises NotFoundException: Если модель не найдена.
        :raises SQLAlchemyError: Если произошла ошибка базы данных.
        :raises ExceptionBase: Если возникла неожиданная ошибка.
        """
        entity = await self._session.get(self.model, id)

        if not entity:
            logger.warning(f"Модель {self.model_name} с ID '{id}' не найдена")
            raise NotFoundException(
                error_message=f"Модель {self.model_name} с ID '{id}' не найдена",
                class_name=self.model_name
            )

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
        """
        Удаляет несколько объектов по их ID.
        Возвращает количество удаленных объектов.
        """
        if not ids:
            return 0

        stmt = delete(self.model).where(self.model.id.in_(ids))
        result = await self._session.execute(stmt)

        deleted_count = result.rowcount
        logger.info(f"Помечено для удаления {deleted_count} объектов {self.model_name}")
        return deleted_count

    @with_read_operation_handling("Ошибка при подсчете записей")
    async def count(self, filters: Optional[Dict] = None) -> int:
        """
        Возвращает число записей в БД.

        :param filters: Фильтры для подсчёта
        :return: Число объектов
        """
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