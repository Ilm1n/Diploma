from light_task.src.config import settings
from light_task.src.utils.file_validator import FileValidator

valid_avatar = FileValidator(
    max_size=settings.files.avatar_max_size,
    allowed_mimes=settings.files.avatar_allowed_types,
)
