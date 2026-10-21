"""Сценарии работы бота: пересчёт бюджетов, сброс остатков, проверка расхода."""

from dataclasses import dataclass

from app.budget.models import AnyExpense, Budget, ExpenseKind, SplitExpense
from app.budget.parsers import parse_budget, parse_expense
from app.budget.rules import budgets_for_recalculation, charge, matching_budgets
from app.config import RECALCULATION_SOURCES, FormId, Settings
from app.pyrus.client import PyrusClient


@dataclass(eq=False)
class _Charge:
    budget: Budget
    expense: AnyExpense


class BudgetService:
    def __init__(self, pyrus: PyrusClient, settings: Settings):
        self._pyrus = pyrus
        self._settings = settings

    def recalculate(self) -> None:
        """Полный пересчёт: остаток каждого бюджета = бюджет минус все его расходы.

        Расходы списываются в порядке создания; каждому проставляется
        «Превышение лимита», затем в БДР записываются новые остатки.
        """
        budgets = self._load_budgets(use_remaining=False)

        charges: list[_Charge] = []
        for form_id, kind in RECALCULATION_SOURCES:
            expenses = [
                parse_expense(kind, t) for t in self._pyrus.get_form_tasks(form_id)
            ]
            for expense in expenses:
                for budget in budgets_for_recalculation(expense, budgets):
                    charges.append(_Charge(budget, expense))

        charges.sort(key=lambda c: c.expense.create_date)
        for c in charges:
            charge(c.budget, c.expense)
            self._save_over_limit(c.expense)
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
        value = "checked" if expense.is_over_limit else "unchecked"
        self._pyrus.update_fields(expense.id, [{"id": field_id, "value": value}])

    def _save_remaining(self, budget: Budget) -> None:
        field_id = self._settings.budget_remaining_field_id
        self._pyrus.update_fields(
            budget.id, [{"id": field_id, "value": budget.remaining}]
        )
