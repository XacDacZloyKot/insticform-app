from fastapi import Depends

from src.db.connection import get_uow_dependency
from src.db.uow import UnitOfWork
from src.repositories.academic_repository import GroupRepository, DisciplineRepository
from src.repositories.test_repository import TestRepository, QuestionRepository, AnswerOptionRepository, \
    TestMediaRepository
from src.repositories.attempt_repository import AttemptRepository, ProctoringRepository
from src.repositories.user_repository import UserRepository
from src.services.academic_service import AcademicService
from src.services.test_service import TestService
from src.services.user_service import UserService
from src.services.attempt_service import AttemptService


def get_user_repository(uow: UnitOfWork = Depends(get_uow_dependency)) -> UserRepository:
    """
    Создает репозиторий пользователей.
    FastAPI создает uow, а мы достаем из него сессию и прокидываем в репозиторий.
    """
    return UserRepository(uow.session)


def get_group_repository(uow: UnitOfWork = Depends(get_uow_dependency)) -> GroupRepository:
    """
    Создает репозиторий групп.
    """
    return GroupRepository(uow.session)


def get_discipline_repository(uow: UnitOfWork = Depends(get_uow_dependency)) -> DisciplineRepository:
    """
    Создает репозиторий дисциплин.
    """
    return DisciplineRepository(uow.session)


def get_test_repository(uow: UnitOfWork = Depends(get_uow_dependency)) -> TestRepository:
    """
    Создает репозиторий тестов.
    """
    return TestRepository(uow.session)


def get_question_repository(uow: UnitOfWork = Depends(get_uow_dependency)) -> QuestionRepository:
    """
    Создает репозиторий вопросов.
    """
    return QuestionRepository(uow.session)


def get_answer_option_repository(uow: UnitOfWork = Depends(get_uow_dependency)) -> AnswerOptionRepository:
    """
    Создает репозиторий вариантов ответа.
    """
    return AnswerOptionRepository(uow.session)


def get_test_media_repository(uow: UnitOfWork = Depends(get_uow_dependency)) -> TestMediaRepository:
    """
    Создает репозиторий медиа.
    """
    return TestMediaRepository(uow.session)

def get_attempt_repository(uow: UnitOfWork = Depends(get_uow_dependency)) -> AttemptRepository:
    """
    Создает репозиторий ответов на вопросы.
    """
    return AttemptRepository(uow.session)

def get_proctoring_repository(uow: UnitOfWork = Depends(get_uow_dependency)) -> ProctoringRepository:
    """
    Создает репозиторий для сбора статистики прокторинга.
    """
    return ProctoringRepository(uow.session)


def get_user_service(repository: UserRepository = Depends(get_user_repository)) -> UserService:
    """Создает сервис пользователей, прокидывая в него репозиторий пользователей."""
    return UserService(repository)


def get_academic_service(
        group_repo: GroupRepository = Depends(get_group_repository),
        discipline_repo: DisciplineRepository = Depends(get_discipline_repository)) -> AcademicService:
    """Создает сервис для академических сущностей, прокидывая в него репозитории групп и дисциплин."""
    return AcademicService(group_repo, discipline_repo)


def get_test_service(
        test_repo: TestRepository = Depends(get_test_repository),
        question_repo: QuestionRepository = Depends(get_question_repository),
        option_repo: AnswerOptionRepository = Depends(get_answer_option_repository),
        media_repo: TestMediaRepository = Depends(get_test_media_repository)
) -> TestService:
    """Создает сервис для тестов, прокидывая в него репозитории вопросов, медиа и опций."""
    return TestService(test_repo, question_repo, option_repo, media_repo)

def get_attempt_service(
        attempt_repo: AttemptRepository = Depends(get_attempt_repository),
        proctoring_repo: ProctoringRepository = Depends(get_proctoring_repository)
) -> AttemptService:
    """Создает сервис для прохождения теста (варианты ответа, прокторинг)"""
    return AttemptService(attempt_repo, proctoring_repo)
