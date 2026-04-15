from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import selectinload

from src.core.utils.file_helper import save_upload_file, delete_physical_file
from src.model.domain.attempt import TestAttempt
from src.model.domain.test import Question, AnswerOption, Test, TestMedia
from src.model.schemas.test import QuestionCreate
from src.repositories.test_repository import TestRepository, TestMediaRepository, QuestionRepository, \
    AnswerOptionRepository


class TestService:
    def __init__(self,
                 test_repo: TestRepository,
                 question_repo: QuestionRepository,
                 option_repo: AnswerOptionRepository,
                 media_repo: TestMediaRepository):
        self.test_repo = test_repo
        self.question_repo = question_repo
        self.option_repo = option_repo
        self.media_repo = media_repo

    async def create_test(self, test_data: dict) -> Test:
        """Создает пустую оболочку теста."""
        new_test = Test(**test_data)
        return await self.test_repo.create(new_test)

    async def attach_media_to_test(self, test_id: int, file: UploadFile) -> TestMedia:
        # Сохраняем файлы на комп
        relative_path, media_type = await save_upload_file(file)

        new_media = TestMedia(
            test_id=test_id,
            file_path=relative_path,
            media_type=media_type,
            original_filename=file.filename
        )
        return await self.media_repo.create(new_media)

    async def list_tests(self) -> List[Test]:
        """Возвращает список всех тестов вместе с их дисциплинами."""
        joins = [selectinload(Test.discipline)]
        return await self.test_repo.list_with_joins(joins=joins)

    async def get_test_by_id(self, test_id: int) -> Test:
        """Получает полную информацию о тесте, включая вопросы, ответы и дисциплину."""
        joins = [
            selectinload(Test.discipline),
            selectinload(Test.creator),
            selectinload(Test.questions).selectinload(Question.options),
            selectinload(Test.media_files),
            selectinload(Test.assigned_students),
            selectinload(Test.attempts).selectinload(TestAttempt.student)
        ]
        return await self.test_repo.get_one_with_joins(id=test_id, joins=joins)

    async def create_question_with_options(
            self, test_id: int, question_data: QuestionCreate, file: Optional[UploadFile] = None
    ) -> Question:

        media_path = None
        media_type = None

        # Если файл передан, сохраняем его
        if file and file.filename:
            media_path, media_type = await save_upload_file(file)

        new_question = Question(
            test_id=test_id,
            text=question_data.text,
            type=question_data.type,
            media_url=media_path,  # Здесь хранится локальный путь (например /images/вывы.png)
            media_type=media_type,  # Сохраняем тип
            allow_partial_credit=question_data.allow_partial_credit,
            time_limit_seconds=question_data.time_limit_seconds
        )
        created_question = await self.question_repo.create(new_question)

        # Сохраняем варианты ответов
        for opt in question_data.options:
            new_option = AnswerOption(
                question_id=created_question.id,
                text=opt.text,
                is_correct=opt.is_correct,
                score_weight=opt.score_weight
            )
            await self.option_repo.create(new_option)

        return created_question

    async def delete_test(self, test_id: int) -> None:
        """Удаляет тест и все связанные с ним физические файлы."""
        test = await self.get_test_by_id(test_id)

        for media in test.media_files:
            delete_physical_file(media.file_path)

        for question in test.questions:
            if question.media_url:
                delete_physical_file(question.media_url)

        await self.test_repo.delete(test_id)

    async def delete_question(self, question_id: int) -> None:
        """Удаляет вопрос и его физический медиафайл."""
        question = await self.question_repo.get_one(id=question_id)
        if question.media_url:
            delete_physical_file(question.media_url)
        await self.question_repo.delete(question_id)

    async def delete_test_media(self, media_id: int) -> None:
        """Удаляет конкретный прикрепленный файл теста."""
        media = await self.media_repo.get_one(id=media_id)
        delete_physical_file(media.file_path)
        await self.media_repo.delete(media_id)

    async def delete_question_media(self, question_id: int) -> None:
        """Удаляет только медиафайл у вопроса, оставляя сам вопрос."""
        question = await self.question_repo.get_one(id=question_id)
        if question.media_url:
            delete_physical_file(question.media_url)
            await self.question_repo.remove_media(question)

    async def assign_students(self, test_id: int, students: list) -> None:
        """Массово назначает тест списку студентов (игнорируя дубликаты)."""
        test = await self.get_test_by_id(test_id)
        await self.test_repo.assign_students(test, students)

    async def unassign_student(self, test_id: int, student_id: int) -> None:
        """Снимает назначение теста с конкретного студента."""
        test = await self.get_test_by_id(test_id)
        student_to_remove = next((s for s in test.assigned_students if s.id == student_id), None)
        if student_to_remove:
            await self.test_repo.unassign_student(test, student_to_remove)
