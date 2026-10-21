"""Разбор задач Pyrus (JSON) в доменные модели.

Правила разбора намеренно повторяют исходную логику один в один,
включая её странности — см. раздел «Известные проблемы» в README.
"""

from collections.abc import Callable, Iterable, Iterator
from datetime import datetime
from typing import Any

from app.budget.models import (
    DEFAULT_DATE,
    AnyExpense,
    Budget,
    Expense,
    ExpenseKind,
    SplitExpense,
    UnitSum,
)

_MISSING: Any = object()


class MissingFieldError(ValueError):
    """В задаче нет поля, без которого её нельзя обработать."""


def _required(value: Any, name: str) -> Any:
    if value is _MISSING:
        raise MissingFieldError(f"В задаче нет поля «{name}»")
    return value


def _catalog_values(value: dict | None) -> list[str] | None:
    """Значения поля-справочника."""
    return value.get("values") if value is not None else None


def _catalog_values_or_choices(value: dict | None) -> list[str] | None:
    """Значения справочника, а если их нет — названия выбранных вариантов."""
    if value is None:
        return None
    if value.get("values") is not None:
        return value.get("values")
    return value.get("choice_names")


def _parse_datetime(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


# ---------- Бюджет БДР ----------


def parse_budget(task: dict, use_remaining: bool) -> Budget:
    """use_remaining=True — взять текущий «Остаток»; иначе остаток = весь бюджет."""
    articles = units = date_from = date_to = amount = _MISSING
    remaining: Any = 0

    for f in task.get("fields"):
        name, value = f["name"], f.get("value")
        if name == "Статья расходов":
            articles = _catalog_values(value)
        elif name == "Подразделения 1С":
            units = _catalog_values(value)
        elif name == "От":
            date_from = value
        elif name == "До":
            date_to = value
        elif name == "Бюджет":
            amount = value
        elif name == "Остаток":
            remaining = value

    if not use_remaining or remaining == 0 or remaining is None:
        remaining = _required(amount, "Бюджет")

    date_from = _required(date_from, "От")
    if date_from:
        date_to = _required(date_to, "До")
    if not date_from or not date_to:
        date_from = date_to = DEFAULT_DATE

    return Budget(
        id=task.get("id"),
        articles=_required(articles, "Статья расходов") or [""],
        units=_required(units, "Подразделения 1С") or [],
        date_from=date_from,
        date_to=date_to,
        remaining=remaining,
    )


# ---------- Счета ----------


def parse_account(task: dict) -> Expense:
    fields = task.get("fields")
    create_date = _parse_datetime(task.get("create_date"))
    date = articles = article_bdr = _MISSING
    units = total = None

    for f in fields:
        name = f["name"]
        if name == "Дата счета":
            date = f.get("value")
        elif name == "Подразделение":
            units = f.get("value").get("values")
        elif name == "Статья расходов":
            articles = _catalog_values(f.get("value"))
        elif name == "Статья БДР":
            article_bdr = _catalog_values(f.get("value"))
        elif name == "Сумма":
            total = f.get("value")

    # Если «Статья расходов» пустая — берём «Статью БДР».
    articles = _required(articles, "Статья расходов")
    article_bdr = _required(article_bdr, "Статья БДР")
    if not articles:
        articles = article_bdr
    if not article_bdr and not articles:
        articles = [""]

    return Expense(
        kind=ExpenseKind.ACCOUNT,
        id=task.get("id"),
        create_date=create_date,
        articles=articles,
        units=units,
        date=_required(date, "Дата счета") or DEFAULT_DATE,
        total=total,
    )


# ---------- Наличные ----------


def _parse_cash(
    task: dict,
    kind: ExpenseKind,
    read_articles: Callable[[dict | None], list[str] | None],
) -> Expense:
    fields = task.get("fields")
    create_date = _parse_datetime(task.get("create_date"))
    date = _MISSING
    units = articles = total = None

    for f in fields:
        name = f["name"]
        if name == "Дата расхода":
            date = f.get("value")
        elif name == "Подразделение":
            units = _catalog_values(f.get("value"))
        elif name == "Статья расходов":
            articles = read_articles(f.get("value"))
        elif name == "Сумма":
            total = f.get("value")

    return Expense(
        kind=kind,
        id=task.get("id"),
        create_date=create_date,
        articles=articles,
        units=units,
        date=_required(date, "Дата расхода") or DEFAULT_DATE,
        total=total,
    )


def parse_cash(task: dict) -> Expense:
    return _parse_cash(task, ExpenseKind.CASH, _catalog_values)


def parse_cash_new(task: dict) -> Expense:
    return _parse_cash(task, ExpenseKind.CASH_NEW, _catalog_values_or_choices)


# ---------- Платежи с разбивкой по подразделениям ----------


def _parse_unit_sums(rows: Iterable[dict] | None) -> Iterator[UnitSum]:
    for row in rows or []:
        cells = row.get("cells") or []
        if len(cells) < 2:
            continue
        unit_cell = cells[0].get("value") if cells[0] else None
        total = cells[1].get("value") if cells[1] else None
        unit = unit_cell.get("values") if isinstance(unit_cell, dict) else None
        if unit is None or total is None:
            continue
        yield UnitSum(unit=unit, total=total)


def _parse_split(
    task: dict,
    kind: ExpenseKind,
    read_articles: Callable[[dict | None], list[str] | None],
) -> SplitExpense:
    fields = task.get("fields") or []
    expense = SplitExpense(
        kind=kind,
        id=task.get("id"),
        create_date=_parse_datetime(task.get("create_date")),
        articles=None,
        date=None,
    )
    article_bdr = None

    for f in fields:
        name, value = f["name"], f.get("value")
        if name == "Дата":
            expense.date = (
                value if value is not None else expense.create_date.strftime("%Y-%m-%d")
            )
        elif name == "Статья расходов":
            expense.articles = read_articles(value)
        elif name == "Статья БДР":
            article_bdr = _catalog_values(value)
        elif name == "Суммы по подразделениям":
            expense.unit_sums.extend(_parse_unit_sums(value))

        # Подстановка значений по умолчанию идёт после КАЖДОГО поля (так в
        # исходной логике), поэтому результат зависит от порядка полей.
        if not expense.articles:
            expense.articles = article_bdr
        if not article_bdr and not expense.articles:
            expense.articles = [""]
        if not expense.date:
            expense.date = DEFAULT_DATE

    return expense


def parse_payment(task: dict) -> SplitExpense:
    return _parse_split(task, ExpenseKind.PAYMENT, _catalog_values)


def parse_payment_new(task: dict) -> SplitExpense:
    return _parse_split(task, ExpenseKind.PAYMENT_NEW, _catalog_values_or_choices)


EXPENSE_PARSERS: dict[ExpenseKind, Callable[[dict], AnyExpense]] = {
    ExpenseKind.ACCOUNT: parse_account,
    ExpenseKind.CASH: parse_cash,
    ExpenseKind.CASH_NEW: parse_cash_new,
    ExpenseKind.PAYMENT: parse_payment,
    ExpenseKind.PAYMENT_NEW: parse_payment_new,
}


def parse_expense(kind: ExpenseKind, task: dict) -> AnyExpense:
    return EXPENSE_PARSERS[kind](task)
