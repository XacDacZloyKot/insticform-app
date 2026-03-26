import logging
import os
import shutil
import uuid

from fastapi import UploadFile, HTTPException, status

from src.model.domain.enums import MediaType

logger = logging.getLogger(__name__)

MEDIA_BASE_DIR = "src/static/media"


async def save_upload_file(upload_file: UploadFile) -> tuple[str, MediaType]:
    """
    Сохраняет файл на диск и возвращает относительный путь и тип медиа.
    """
    # Определяем тип медиа
    content_type = upload_file.content_type
    if content_type.startswith("image/"):
        media_type = MediaType.IMAGE
        sub_dir = "images"
    elif content_type.startswith("video/"):
        media_type = MediaType.VIDEO
        sub_dir = "videos"
    elif content_type.startswith("audio/"):
        media_type = MediaType.AUDIO
        sub_dir = "audios"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неподдерживаемый тип файла")

    # Создаем папку, если её нет
    target_dir = os.path.join(MEDIA_BASE_DIR, sub_dir)
    os.makedirs(target_dir, exist_ok=True)

    # Генерируем уникальное имя файла
    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(target_dir, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    # Относительный путь для сохранения в БД
    relative_path = f"/{sub_dir}/{unique_filename}"

    return relative_path, media_type


def delete_physical_file(relative_path: str) -> None:
    """Удаляет физический файл с диска по его относительному пути."""
    if not relative_path:
        return

    # Убираем начальный сле (images/dasds.png)
    clean_path = relative_path.lstrip("/")
    full_path = os.path.join(MEDIA_BASE_DIR, clean_path)

    if os.path.exists(full_path):
        try:
            os.remove(full_path)
            logger.info(f"Файл успешно удален с диска: {full_path}")
        except Exception as e:
            logger.error(f"Ошибка при удалении файла {full_path}: {e}")
