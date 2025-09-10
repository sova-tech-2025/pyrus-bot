import os

import requests

BASE_URL = "https://api.pyrus.com/v4"

def auth() -> str:
    url = f"{BASE_URL}/auth"

    body = {
        "login": os.getenv("BOT_LOGIN"),
        "security_key": os.getenv("BOT_SECRET_KEY"),
    }

    try:
        with requests.Session() as session:
            response = session.post(url, json=body, timeout=10)
            response.raise_for_status()

            data = response.json()
            access_token = data.get("access_token")

            return access_token

    except requests.exceptions.Timeout:
        print("Запрос превысил таймаут")
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP ошибка: {errh}")
    except requests.exceptions.RequestException as err:
        print(f"Ошибка запроса: {err}")
    except ValueError:
        print("Ответ не является JSON")


def get_form_budget_BDR(ctx):
    url = f"{BASE_URL}/forms/2346023/register"
    headers = {
        'Authorization': f'Bearer {ctx["access_token"]}',
        'Content-Type': 'application/json'
    }

    try:
        with requests.Session() as session:
            session.headers.update(headers)
            response = session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            tasks = data.get('tasks')

            return tasks

    except requests.exceptions.Timeout:
        print("Запрос превысил таймаут")
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP ошибка: {errh}")
    except requests.exceptions.RequestException as err:
        print(f"Ошибка запроса: {err}")
    except ValueError:
        print("Ответ не является JSON")

def get_form_accounts(ctx):
    url = f"{BASE_URL}/forms/2336661/register"
    headers = {
        'Authorization': f'Bearer {ctx["access_token"]}',
        'Content-Type': 'application/json'
    }

    try:
        with requests.Session() as session:
            session.headers.update(headers)
            response = session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            tasks = data.get('tasks')

            return tasks

    except requests.exceptions.Timeout:
        print("Запрос превысил таймаут")
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP ошибка: {errh}")
    except requests.exceptions.RequestException as err:
        print(f"Ошибка запроса: {err}")
    except ValueError:
        print("Ответ не является JSON")

def get_form_cash(ctx):
    url = f"{BASE_URL}/forms/2346729/register"
    headers = {
        'Authorization': f'Bearer {ctx["access_token"]}',
        'Content-Type': 'application/json'
    }

    try:
        with requests.Session() as session:
            session.headers.update(headers)
            response = session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            tasks = data.get('tasks')

            return tasks

    except requests.exceptions.Timeout:
        print("Запрос превысил таймаут")
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP ошибка: {errh}")
    except requests.exceptions.RequestException as err:
        print(f"Ошибка запроса: {err}")
    except ValueError:
        print("Ответ не является JSON")

def set_field_comment_BDR(ctx, task_id, body):
    url = f"{BASE_URL}/tasks/{task_id}/comments"
    headers = {
        'Authorization': f'Bearer {ctx["access_token"]}',
        'Content-Type': 'application/json'
    }

    try:
        with requests.Session() as session:
            session.headers.update(headers)
            response = session.post(url, json=body, timeout=10)
            response.raise_for_status()

            data = response.json()
            tasks = data.get('tasks')

            return tasks

    except requests.exceptions.Timeout:
        print("Запрос превысил таймаут")
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP ошибка: {errh}")
    except requests.exceptions.RequestException as err:
        print(f"Ошибка запроса: {err}")
    except ValueError:
        print("Ответ не является JSON")

def set_field_comment_counts(ctx, task_id, body):
    url = f"{BASE_URL}/tasks/{task_id}/comments"
    headers = {
        'Authorization': f'Bearer {ctx["access_token"]}',
        'Content-Type': 'application/json'
    }

    try:
        with requests.Session() as session:
            session.headers.update(headers)
            response = session.post(url, json=body, timeout=10)
            response.raise_for_status()

            data = response.json()
            tasks = data.get('tasks')

            return tasks

    except requests.exceptions.Timeout:
        print("Запрос превысил таймаут")
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP ошибка: {errh}")
    except requests.exceptions.RequestException as err:
        print(f"Ошибка запроса: {err}")
    except ValueError:
        print("Ответ не является JSON")