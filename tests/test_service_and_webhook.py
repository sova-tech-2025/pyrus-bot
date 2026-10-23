import hashlib
import hmac
import json

from app.budget.models import ExpenseKind
from app.budget.service import BudgetService
from app.config import FormId, Settings
from app.web.webhook import ERROR_TEXT, WebhookHandler, is_signature_valid

SETTINGS = Settings(
    bot_login="bot",
    bot_secret_key="secret",
    budget_remaining_field_id=10,
    account_overlimit_field_id="57",
    cash_overlimit_field_id="16",
    payment_overlimit_field_id="27",
    cash_new_overlimit_field_id="14",
    payment_new_overlimit_field_id="17",
)


class FakePyrus:
    def __init__(self, forms):
        self.forms = forms
        self.updates = []

    def get_form_tasks(self, form_id):
        return self.forms.get(form_id, [])

    def update_fields(self, task_id, updates):
        self.updates.append((task_id, updates))


def f(name, value):
    return {"name": name, "value": value}


BDR = {
    "id": 1,
    "fields": [
        f("Статья расходов", {"values": ["A"]}),
        f("Подразделения 1С", {"values": ["U1"]}),
        f("От", "2025-01-01"),
        f("До", "2025-12-31"),
        f("Бюджет", 100),
        f("Остаток", 40),
    ],
}


def account(task_id, total):
    return {
        "id": task_id,
        "create_date": f"2025-02-0{task_id % 10}T00:00:00Z",
        "fields": [
            f("Дата счета", "2025-03-01"),
            f("Подразделение", {"values": ["U1"]}),
            f("Статья расходов", {"values": ["A"]}),
            f("Статья БДР", None),
            f("Сумма", total),
        ],
    }


def payment(task_id, total):
    return {
        "id": task_id,
        "create_date": "2025-02-01T00:00:00Z",
        "fields": [
            f("Дата", "2025-03-01"),
            f("Статья расходов", {"values": ["A"]}),
            f(
                "Суммы по подразделениям",
                [{"cells": [{"value": {"values": ["U1"]}}, {"value": total}]}],
            ),
        ],
    }


def test_recalculate_writes_flags_then_remaining():
    pyrus = FakePyrus(
        {FormId.BDR: [BDR], FormId.ACCOUNTS: [account(2, 70), account(3, 50)]}
    )
    BudgetService(pyrus, SETTINGS).recalculate()
    assert pyrus.updates == [
        (2, [{"id": "57", "value": "unchecked"}]),
        (3, [{"id": "57", "value": "checked"}]),
        (1, [{"id": 10, "value": 30}]),
        (1, [{"id": 10, "value": 30}]),
    ]


def bdr_for_unit(task_id, unit, budget):
    return {
        "id": task_id,
        "fields": [
            f("Статья расходов", {"values": ["A"]}),
            f("Подразделения 1С", {"values": [unit]}),
            f("От", "2025-01-01"),
            f("До", "2025-12-31"),
            f("Бюджет", budget),
        ],
    }


def split_payment(task_id, sums, flag):
    rows = [{"cells": [{"value": {"values": [u]}}, {"value": t}]} for u, t in sums]
    return {
        "id": task_id,
        "create_date": "2025-02-01T00:00:00Z",
        "fields": [
            f("Дата", "2025-03-01"),
            f("Статья расходов", {"values": ["A"]}),
            f("Суммы по подразделениям", rows),
            {"id": 27, "name": "Превышение лимита", "value": flag},
        ],
    }


def flag_writes(pyrus, task_id):
    return [u for tid, u in pyrus.updates if tid == task_id]


def test_split_payment_flag_is_written_once_with_final_value():
    """Баг с уведомлениями: платёж на несколько подразделений, в одном не хватает
    бюджета. Раньше галочка прыгала «снята → стоит» десятки раз за пересчёт."""
    budgets = [bdr_for_unit(1, "U1", 1000), bdr_for_unit(2, "U2", 10)]
    pay = split_payment(5, [("U1", 50), ("U2", 50)], "unchecked")
    pyrus = FakePyrus({FormId.BDR: budgets, FormId.PAYMENTS: [pay]})

    BudgetService(pyrus, SETTINGS).recalculate()

    assert flag_writes(pyrus, 5) == [[{"id": "27", "value": "checked"}]]


def test_unchanged_flag_is_not_rewritten():
    """Если галочка в Pyrus уже правильная, бот её не трогает,
    и маршрут задачи не перестраивается."""
    budgets = [bdr_for_unit(1, "U1", 1000), bdr_for_unit(2, "U2", 10)]
    pay = split_payment(5, [("U1", 50), ("U2", 50)], "checked")
    pyrus = FakePyrus({FormId.BDR: budgets, FormId.PAYMENTS: [pay]})

    BudgetService(pyrus, SETTINGS).recalculate()

    assert flag_writes(pyrus, 5) == []


def test_reset_remaining_sets_full_budget():
    pyrus = FakePyrus({FormId.BDR: [BDR]})
    BudgetService(pyrus, SETTINGS).reset_remaining()
    assert pyrus.updates == [(1, [{"id": 10, "value": 100}])]


def test_check_payment_over_current_remaining():
    pyrus = FakePyrus({FormId.BDR: [BDR]})
    over = BudgetService(pyrus, SETTINGS).check_expense(
        ExpenseKind.PAYMENT, payment(5, 50)
    )
    assert over is True
    assert pyrus.updates == [
        (5, [{"id": "27", "value": "checked"}]),
        (1, [{"id": 10, "value": 40}]),
    ]


def test_signature():
    body = b'{"a": 1}'
    sig = hmac.new(b"secret", body, hashlib.sha1).hexdigest()
    assert is_signature_valid(body, "secret", sig.upper())
    assert not is_signature_valid(body, "secret", "bad")


class StubService:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def check_expense(self, kind, task):
        self.calls.append(kind)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def webhook_body(event="comment", form_id=FormId.PAYMENTS, step=1):
    return json.dumps(
        {"event": event, "task": {"form_id": form_id, "current_step": step}}
    )


def test_webhook_decisions():
    assert WebhookHandler(StubService(True)).handle(webhook_body()) == {
        "approval_choice": "rejected"
    }
    assert WebhookHandler(StubService(False)).handle(webhook_body()) == {
        "approval_choice": "approved"
    }
    assert WebhookHandler(StubService(None)).handle(webhook_body()) == {
        "approval_choice": "approved"
    }
    assert WebhookHandler(StubService(RuntimeError())).handle(webhook_body()) == {
        "text": ERROR_TEXT
    }


def test_webhook_ignores_other_events_with_error_text():
    stub = StubService(True)
    handler = WebhookHandler(stub)
    for body in (
        webhook_body(event="task_received"),
        webhook_body(step=2),
        webhook_body(form_id=FormId.BDR),
    ):
        assert handler.handle(body) == {"text": ERROR_TEXT}
    assert stub.calls == []
