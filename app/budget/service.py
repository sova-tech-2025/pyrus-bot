"""Сценарии работы бота: пересчёт бюджетов, сброс остатков, проверка расхода."""

from dataclasses import dataclass
from typing import Any

from app.budget.models import AnyExpense, Budget, ExpenseKind, SplitExpense
from app.budget.parsers import parse_budget, parse_expense
from app.budget.rules import budgets_for_recalculation, charge, matching_budgets
from app.config import RECALCULATION_SOURCES, FormId, Settings
from app.pyrus.client import PyrusClient

CHECKED, UNCHECKED = "checked", "unchecked"
_NOT_FOUND: Any = object()


@dataclass(eq=False)
class _Charge:
    budget: Budget
    expense: AnyExpense


def _field_value(task: dict, field_id: Any) -> Any:
    """Текущее значение поля задачи по его ID (или _NOT_FOUND)."""
    for f in task.get("fields") or []:
        if str(f.get("id")) == str(field_id):
            return f.get("value") or UNCHECKED  # пустой чекбокс = снят
    return _NOT_FOUND


class BudgetService:
    def __init__(self, pyrus: PyrusClient, settings: Settings):
        self._pyrus = pyrus
        self._settings = settings

    def recalculate(self) -> None:
        """Полный пересчёт: остаток каждого бюджета = бюджет минус все его расходы.

        Расходы списываются в порядке создания, затем в каждом расходе
        выставляется «Превышение лимита», а в БДР записываются новые остатки.
        """
        budgets = self._load_budgets(use_remaining=False)

        charges: list[_Charge] = []
        saved_flags: dict[
            tuple[Any, Any], Any
        ] = {}  # (задача, поле) -> значение в Pyrus
        for form_id, kind in RECALCULATION_SOURCES:
            tasks = self._pyrus.get_form_tasks(form_id)
            expenses = [parse_expense(kind, t) for t in tasks]
            field_id = self._settings.overlimit_field_id(kind)
            for task in tasks:
                saved_flags[(task.get("id"), field_id)] = _field_value(task, field_id)
            for expense in expenses:
                for budget in budgets_for_recalculation(expense, budgets):
                    charges.append(_Charge(budget, expense))

        # Один платёж может списываться с нескольких бюджетов (по подразделениям)
        # и попадать в пересчёт несколько раз. Раньше галочка писалась после
        # каждого списания и прыгала «снята → стоит → снята», а каждое её изменение
        # заставляет Pyrus перестраивать маршрут задачи и слать уведомления.
        # Теперь пишем один раз итоговое значение и только если оно изменилось.
        charges.sort(key=lambda c: c.expense.create_date)
        final_flags: dict[tuple[Any, Any], str] = {}
        for c in charges:
            charge(c.budget, c.expense)
            key = (c.expense.id, self._settings.overlimit_field_id(c.expense.kind))
            final_flags[key] = CHECKED if c.expense.is_over_limit else UNCHECKED

        for (task_id, field_id), value in final_flags.items():
            if saved_flags.get((task_id, field_id), _NOT_FOUND) != value:
                self._pyrus.update_fields(task_id, [{"id": field_id, "value": value}])

        for c in charges:  # (!) остаток пишется по разу на каждое списание
            self._save_remaining(c.budget)

    def reset_remaining(self) -> None:
        """Записать в «Остаток» каждого бюджета полную сумму бюджета."""
        for budget in self._load_budgets(use_remaining=False):
            self._save_remaining(budget)

    def check_expense(self, kind: ExpenseKind, task: dict) -> bool | None:
        """Проверка одного расхода из вебхука: списать с текущего остатка.

        Возвращает True, если лимит превышен; None — если подходящего бюджета нет.
        """
        budgets = self._load_budgets(use_remaining=True)
        expense = parse_expense(kind, task)

        budget = next(matching_budgets(expense, budgets), None)
        if budget is None:
            return None

        charge(budget, expense)
        self._save_over_limit(expense)
        self._save_remaining(budget)

        # (!) Для счетов и наличных результат не возвращается — их всегда согласуют.
        return expense.is_over_limit if isinstance(expense, SplitExpense) else None

    def _load_budgets(self, use_remaining: bool) -> list[Budget]:
        return [
            parse_budget(task, use_remaining)
            for task in self._pyrus.get_form_tasks(FormId.BDR)
        ]

    def _save_over_limit(self, expense: AnyExpense) -> None:
        field_id = self._settings.overlimit_field_id(expense.kind)
        value = CHECKED if expense.is_over_limit else UNCHECKED
        self._pyrus.update_fields(expense.id, [{"id": field_id, "value": value}])

    def _save_remaining(self, budget: Budget) -> None:
        field_id = self._settings.budget_remaining_field_id
        self._pyrus.update_fields(
            budget.id, [{"id": field_id, "value": budget.remaining}]
        )
