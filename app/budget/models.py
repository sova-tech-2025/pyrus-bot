"""Доменные модели: бюджет и расходы, которые из него списываются."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel

DEFAULT_DATE = "1900-01-01"


class ExpenseKind(Enum):
    """Вид расхода = форма Pyrus, из которой он пришёл."""

    ACCOUNT = "account"  # Счета
    CASH = "cash"  # Наличные КЕКС
    CASH_NEW = "cash_new"  # Наличные новые
    PAYMENT = "payment"  # Платежи 2 и более ЮЛ
    PAYMENT_NEW = "payment_new"  # Платежи новые


@dataclass(eq=False)
class Budget:
    """Строка формы «Бюджет БДР»."""

    id: Any
    articles: list[str]
    units: list[str]
    date_from: str
    date_to: str
    remaining: Any  # «Остаток»: сколько ещё можно потратить


@dataclass(eq=False)
class Expense:
    """Расход с одной суммой на одно подразделение (счета, наличные)."""

    kind: ExpenseKind
    id: Any
    create_date: datetime
    articles: list[str] | None
    units: list[str] | None
    date: str
    total: Any
    is_over_limit: bool = False


class UnitSum(BaseModel):
    """Строка таблицы «Суммы по подразделениям»."""

    unit: list[str]
    total: float


@dataclass(eq=False)
class SplitExpense:
    """Платёж, разбитый по нескольким подразделениям."""

    kind: ExpenseKind
    id: Any
    create_date: datetime
    articles: list[str] | None
    date: str | None
    unit_sums: list[UnitSum] = field(default_factory=list)
    is_over_limit: bool = False


AnyExpense = Expense | SplitExpense
