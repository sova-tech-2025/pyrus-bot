"""Тонкий клиент Pyrus API v4: только те методы, что нужны боту."""

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.pyrus.com/v4"
TIMEOUT_SECONDS = 10


class PyrusError(RuntimeError):
    """Pyrus ответил не так, как ожидалось."""


_FAILED: Any = object()  # запрос не удался (ошибка уже записана в лог)


class PyrusClient:
    def __init__(self, login: str | None, security_key: str | None):
        self._login = login
        self._security_key = security_key
        # Если авторизация не удалась, токен становится None (как и раньше).
        self._access_token: str | None = ""

    def authenticate(self) -> None:
        """Получить новый токен бота."""
        data = self._request(
            "POST",
            "/auth",
            json={"login": self._login, "security_key": self._security_key},
            authorized=False,
        )
        self._access_token = None if data is _FAILED else data.get("access_token")

    def get_form_tasks(self, form_id: int) -> list[dict]:
        """Задачи из реестра формы. При сетевой ошибке — пустой список."""
        data = self._request("GET", f"/forms/{int(form_id)}/register")
        if data is _FAILED:
            return []
        tasks = data.get("tasks")
        if tasks is None:
            raise PyrusError(f"В ответе реестра формы {form_id} нет задач")
        return tasks

    def update_fields(self, task_id: Any, updates: list[dict]) -> None:
        """Изменить поля задачи (через пустой комментарий)."""
        self._request(
            "POST",
            f"/tasks/{task_id}/comments",
            json={"text": "", "field_updates": updates},
            parse_json=False,
        )

    def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
        authorized: bool = True,
        parse_json: bool = True,
    ) -> Any:
        """Выполняет запрос. При ошибке сети/HTTP/JSON пишет в лог и возвращает _FAILED."""
        headers = {}
        if authorized:
            headers = {
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            }
        try:
            with requests.Session() as session:
                session.headers.update(headers)
                response = session.request(
                    method, BASE_URL + path, json=json, timeout=TIMEOUT_SECONDS
                )
                response.raise_for_status()
                return response.json() if parse_json else None
        except requests.exceptions.Timeout:
            logger.error("Pyrus %s %s: превышен таймаут", method, path)
        except requests.exceptions.HTTPError as error:
            logger.error("Pyrus %s %s: HTTP ошибка: %s", method, path, error)
        except requests.exceptions.RequestException as error:
            logger.error("Pyrus %s %s: ошибка запроса: %s", method, path, error)
        except ValueError:
            logger.error("Pyrus %s %s: ответ не является JSON", method, path)
        return _FAILED
