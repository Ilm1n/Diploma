"""User-facing messages and translations used across the backend.

This module centralises all textual responses that are returned in
`HTTPException.detail` fields. For this iteration we only provide Russian
translations, but in future the dictionary can be extended or wrapped with a
proper internationalisation layer.

Usage example:

    from src.messages import MESSAGES
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail=MESSAGES["PROJECT_NOT_FOUND"])

Or with formatting:

    MESSAGES["INVITATION_EXPIRES_IN"].format(days=3)

"""

from __future__ import annotations

from typing import Dict

# canonical keys for error/status messages
MESSAGES: Dict[str, str] = {
    # authentication
    "INVALID_CREDENTIALS": "Неверное имя пользователя или пароль",
    "TOKEN_EXPIRED": "Срок действия токена истек",
    "COULD_NOT_VALIDATE": "Не удалось проверить учетные данные",
    "REFRESH_TOKEN_MISSING": "Отсутствует refresh token",
    "INVALID_TOKEN_TYPE": "Неверный тип токена",
    "INVALID_TOKEN_PAYLOAD": "Недействительный payload токена",
    "NOT_AUTHENTICATED": "Не авторизован",
    # users
    "USER_NOT_FOUND": "Пользователь не найден",
    "INACTIVE_USER": "Пользователь не активен",
    "USERNAME_OR_EMAIL_EXISTS": "Пользователь с таким именем или почтой уже существует",
    "USERNAME_TAKEN": "Имя пользователя уже занято",
    # projects
    "PROJECT_NOT_FOUND": "Проект не найден",
    "INSUFFICIENT_PERMISSIONS": "У вас недостаточно прав для выполнения этого действия",
    "CANNOT_DELETE_OWNER": "Невозможно удалить владельца проекта",
    # boards / columns / tasks
    "COLUMN_NOT_FOUND": "Колонка не найдена",
    "COLUMN_BELONGS_ANOTHER_PROJECT": "Колонка принадлежит другому проекту",
    "COLUMN_TASK_LIMIT_REACHED": "Достигнут лимит задач в колонке",
    "ASSIGNEE_NOT_PROJECT_MEMBER": "Исполнитель не является участником проекта",
    "INVALID_TAG_IDS": "Некорректные идентификаторы тегов",
    "INVALID_TARGET_COLUMN": "Недопустимая целевая колонка",
    "ANCHOR_TASK_NOT_FOUND": "Опорная задача не найдена",
    "TASK_NOT_FOUND": "Задача не найдена",
    "MEMBERS_ONLY_OWN_TASKS": "Участники могут редактировать только свои собственные задачи",
    # tags
    "TAG_ALREADY_EXISTS": "Тег с таким именем уже существует в проекте",
    # invitations
    "INVITATION_NOT_FOUND": "Приглашение не найдено",
    "INVITATION_EXPIRED": "Срок действия приглашения истек",
    "INVITATION_USAGE_LIMIT_REACHED": "Превышен лимит использования приглашения",
    "INVITATION_FOR_OTHER_EMAIL": "Это приглашение было отправлено другому адресу электронной почты",
    "ALREADY_PROJECT_MEMBER": "Вы уже являетесь участником этого проекта",
    "INVITATION_ACCEPT_SUCCESS": "Успешно присоединились к проекту",
    "MEMBER_NOT_FOUND": "Участник не найден",
    "NOT_A_PROJECT_MEMBER": "Вы не являетесь участником этого проекта",
    "CANNOT_REMOVE_OWNER": "Нельзя удалить владельца проекта",
    "MANAGERS_CANNOT_REMOVE": "Менеджеры не могут удалять других менеджеров. Обратитесь к владельцу.",
    "CANNOT_CHANGE_OWNER_ROLE": "Нельзя изменить роль владельца проекта",
    # generic
    "DATABASE_ERROR": "Ошибка базы данных",
    "FILE_UPLOAD_FAILED": "Не удалось загрузить файл",
    "DB_COMMIT_FAILED": "Ошибка сохранения в базе данных",
}
