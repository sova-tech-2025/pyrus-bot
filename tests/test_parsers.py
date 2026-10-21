import pytest

from app.budget.models import DEFAULT_DATE
from app.budget.parsers import MissingFieldError, parse_budget, parse_payment


def field(name, value):
    return {"id": 1, "name": name, "value": value}


def bdr_task(**overrides):
    values = {
        "Статья расходов": {"values": ["A"]},
        "Подразделения 1С": {"values": ["U1"]},
        "От": "2025-01-01",
        "До": "2025-12-31",
        "Бюджет": 1000,
        "Остаток": 300,
    }
    values.update(overrides)
    return {"id": 5, "fields": [field(k, v) for k, v in values.items()]}


def test_budget_remaining_is_full_budget_on_recalculation():
    assert parse_budget(bdr_task(), use_remaining=False).remaining == 1000


def test_budget_uses_current_remaining_for_webhook():
    assert parse_budget(bdr_task(), use_remaining=True).remaining == 300


def test_budget_zero_remaining_is_treated_as_full_budget():
    assert parse_budget(bdr_task(Остаток=0), use_remaining=True).remaining == 1000


def test_budget_without_end_date_gets_default_period():
    b = parse_budget(bdr_task(До=None), use_remaining=False)
    assert (b.date_from, b.date_to) == (DEFAULT_DATE, DEFAULT_DATE)


def test_budget_empty_catalogs_get_defaults():
    b = parse_budget(
        bdr_task(**{"Статья расходов": None, "Подразделения 1С": None}),
        use_remaining=False,
    )
    assert b.articles == [""]
    assert b.units == []


def test_budget_without_required_field_fails():
    task = bdr_task()
    task["fields"] = [f for f in task["fields"] if f["name"] != "От"]
    with pytest.raises(MissingFieldError):
        parse_budget(task, use_remaining=False)


def test_payment_rows_are_parsed_and_broken_rows_skipped():
    rows = [
        {"cells": [{"value": {"values": ["U1"]}}, {"value": 10}]},
        {"cells": [{"value": {"values": ["U2"]}}]},  # нет суммы
        {"cells": [{"value": "x"}, {"value": 5}]},  # подразделение не справочник
    ]
    task = {
        "id": 1,
        "create_date": "2025-02-01T10:00:00Z",
        "fields": [
            field("Дата", None),
            field("Статья расходов", {"values": ["A"]}),
            field("Суммы по подразделениям", rows),
        ],
    }
    p = parse_payment(task)
    assert p.date == "2025-02-01"  # пустая дата = дата создания
    assert p.articles == ["A"]
    assert [(u.unit, u.total) for u in p.unit_sums] == [(["U1"], 10.0)]
