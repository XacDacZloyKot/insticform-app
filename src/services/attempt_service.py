from sqlalchemy.orm import selectinload

from src.model.domain.attempt import StudentAnswer
from src.model.domain.attempt import TestAttempt, ProctoringEvent
from src.model.domain.enums import AttemptStatus, ProctoringAction
from src.model.domain.test import Test, Question
from src.repositories.attempt_repository import AttemptRepository, ProctoringRepository


class AttemptService:
    def __init__(self, attempt_repo: AttemptRepository, proctoring_repo: ProctoringRepository):
        self.attempt_repo = attempt_repo
        self.proctoring_repo = proctoring_repo

    async def start_attempt(self, test_id: int, student_id: int) -> TestAttempt:
        """Создает новую попытку прохождения (фиксирует время старта)."""
        attempt = TestAttempt(test_id=test_id, student_id=student_id, status=AttemptStatus.IN_PROGRESS)
        return await self.attempt_repo.create(attempt)

    async def get_attempt_with_test(self, attempt_id: int) -> TestAttempt:
        """Подгружает попытку вместе со всеми вопросами и медиафайлами теста."""
        joins = [
            selectinload(TestAttempt.student_answers),
            selectinload(TestAttempt.test).selectinload(Test.media_files),
            selectinload(TestAttempt.test).selectinload(Test.questions).selectinload(Question.options)
        ]
        return await self.attempt_repo.get_one_with_joins(id=attempt_id, joins=joins)

    async def log_proctoring_event(self, attempt_id: int, action: str, details: str = None) -> None:
        """Сохраняет событие прокторинга (например, переключение вкладки)."""
        event = ProctoringEvent(
            attempt_id=attempt_id,
            action_type=ProctoringAction(action),
            details=details
        )
        await self.proctoring_repo.create(event)

    async def finish_attempt(self, attempt_id: int, form_data) -> TestAttempt:
        """Закрывает попытку тестирования, сохраняет ответы и рассчитывает балл."""
        attempt = await self.get_attempt_with_test(attempt_id)

        total_score = 0.0

        for question in attempt.test.questions:
            awarded_score = 0.0
            selected_options = []
            text_answer = None

            # Логика для выбора одного или нескольких вариантов (тесты)
            if question.type.value in ['single_choice', 'multiple_choice']:
                # Получаем все выбранные чекбоксы/радиокнопки для этого вопроса (getlist)
                submitted_values = form_data.getlist(f"q_{question.id}")
                submitted_ids = [int(v) for v in submitted_values if v.isdigit()]

                # Достаем реальные объекты вариантов из БД
                selected_options = [opt for opt in question.options if opt.id in submitted_ids]
                correct_options = [opt for opt in question.options if opt.is_correct]

                set_selected = set(opt.id for opt in selected_options)
                set_correct = set(opt.id for opt in correct_options)

                # Если студент выбрал в точности все правильные варианты
                if set_selected == set_correct and len(set_correct) > 0:
                    awarded_score = sum(opt.score_weight for opt in correct_options)
                # Если частичный балл разрешен (выбрал только часть правильных)
                elif question.allow_partial_credit:
                    score = sum(opt.score_weight for opt in selected_options if opt.is_correct)
                    penalty = sum(opt.score_weight for opt in selected_options if not opt.is_correct)
                    awarded_score = max(0.0, score - penalty)  # Балл не может быть меньше нуля

            # Логика для открытого текстового вопроса (эссе)
            else:
                text_answer = form_data.get(f"q_{question.id}")
                awarded_score = 0.0  # Автопроверку текста реализовать сложно, оставляем 0 до ручной проверки преподавателем

            # Создаем объект ответа студента и прикрепляем к попытке
            student_answer = StudentAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                awarded_score=awarded_score,
                text_answer=text_answer,
                selected_options=selected_options
            )
            attempt.student_answers.append(student_answer)
            total_score += awarded_score

        # Фиксируем общий балл и закрываем попытку
        attempt.total_score = total_score
        await self.attempt_repo.finish_attempt(attempt)

        return attempt

    async def get_full_attempt_details(self, attempt_id: int) -> TestAttempt:
        """Подгружает попытку со всеми деталями (ответы, прокторинг, вопросы)."""
        joins = [
            selectinload(TestAttempt.student),
            selectinload(TestAttempt.test).selectinload(Test.questions).selectinload(Question.options),
            selectinload(TestAttempt.student_answers).selectinload(StudentAnswer.selected_options),
            selectinload(TestAttempt.proctoring_logs)
        ]
        return await self.attempt_repo.get_one_with_joins(id=attempt_id, joins=joins)

    async def clear_proctoring_logs(self, attempt_id: int) -> None:
        """Очищает логи прокторинга для конкретной попытки."""
        await self.proctoring_repo.clear_by_attempt_id(attempt_id)

    async def delete_attempt(self, attempt_id: int) -> int:
        """Удаляет попытку (каскадно удалятся и ответы) и возвращает ID студента для редиректа."""
        attempt = await self.attempt_repo.get_one(id=attempt_id)
        student_id = attempt.student_id
        await self.attempt_repo.delete(attempt_id)
        return student_id
