import requests

BASE_URL = "https://api.pyrus.com/v4"

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