"""Обработка вебхука Pyrus: бот согласует или отклоняет расход на первом этапе."""

import hashlib
import hmac
import json
import logging

from app.budget.models import ExpenseKind
from app.budget.service import BudgetService
from app.config import WEBHOOK_FORMS

logger = logging.getLogger(__name__)

ERROR_TEXT = "Ошибка обработки задачи, свяжитесь с администратором бота"


def is_signature_valid(body: bytes, secret: str, signature: str) -> bool:
    """Подпись Pyrus: HMAC-SHA1 тела запроса ключом бота."""
    digest = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha1).hexdigest()
    return hmac.compare_digest(digest, signature.lower())


def _expense_kind(event: dict, task: dict) -> ExpenseKind | None:
    """Вид расхода, если событие нужно проверять, иначе None."""
    if event.get("event") != "comment":
        return None
    kind = WEBHOOK_FORMS.get(task.get("form_id"))
    if kind is None or task.get("current_step") != 1:
        return None
    return kind


class WebhookHandler:
    def __init__(self, budget_service: BudgetService):
        self._budget_service = budget_service

    def handle(self, body: str) -> dict:
        """Ответ боту Pyrus: approved / rejected или текст ошибки."""
        logger.debug("Incoming body: %s", body)
        event = json.loads(body)
        task = event.get("task", {})

        # (!) На любые другие события бот тоже отвечает текстом ошибки — так было.
        response = {"text": ERROR_TEXT}
        try:
            kind = _expense_kind(event, task)
            if kind is not None:
                over_limit = self._budget_service.check_expense(kind, task)
                choice = "rejected" if over_limit else "approved"
                response = {"approval_choice": choice}
        except Exception:
            logger.exception("Не удалось обработать вебхук")

        logger.debug("Response: %s", response)
        return response
