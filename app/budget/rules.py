"""Бизнес-правила: какой расход к какому бюджету относится и как списывается лимит.

Здесь нет обращений к Pyrus — только чистая логика, её легко тестировать.
"""

from collections.abc import Iterable, Iterator

from app.budget.models import AnyExpense, Budget, Expense, SplitExpense


def _fits(budget: Budget, articles, units, date) -> bool:
    """Совпадает статья, подразделение и дата попадает в период бюджета."""
    return bool(
        (set(articles) & set(budget.articles))
        and "".join(units) == "".join(budget.units)
        and budget.date_from <= date <= budget.date_to
    )


def _expense_fits(budget: Budget, expense: AnyExpense) -> bool:
    if isinstance(expense, SplitExpense):
        return any(
            _fits(budget, expense.articles, unit_sum.unit, expense.date)
            for unit_sum in expense.unit_sums
        )
    return _fits(budget, expense.articles, expense.units, expense.date)


def matching_budgets(
    expense: AnyExpense, budgets: Iterable[Budget]
) -> Iterator[Budget]:
    """Бюджеты, к которым относится расход, по порядку."""
    return (budget for budget in budgets if _expense_fits(budget, expense))


def budgets_for_recalculation(
    expense: AnyExpense, budgets: Iterable[Budget]
) -> list[Budget]:
    """Счёт/наличные списываются с первого подходящего бюджета,
    платёж с разбивкой — со всех подходящих."""
    found = matching_budgets(expense, budgets)
    if isinstance(expense, SplitExpense):
        return list(found)
    first = next(found, None)
    return [first] if first is not None else []


def charge(budget: Budget, expense: AnyExpense) -> None:
    """Списывает расход с остатка бюджета и проставляет признак превышения."""
    if isinstance(expense, SplitExpense):
        _charge_split(budget, expense)
    else:
        _charge_single(budget, expense)


def _charge_single(budget: Budget, expense: Expense) -> None:
    if budget.remaining >= expense.total:
        budget.remaining -= expense.total
        expense.is_over_limit = False
    else:
        expense.is_over_limit = True


def _charge_split(budget: Budget, expense: SplitExpense) -> None:
    # Сначала крупные суммы. Признак превышения только включается и не сбрасывается.
    expense.unit_sums.sort(key=lambda unit_sum: unit_sum.total, reverse=True)
    exceeded = False
    for unit_sum in expense.unit_sums:
        if not _fits(budget, expense.articles, unit_sum.unit, expense.date):
            continue
        if budget.remaining >= unit_sum.total:
            budget.remaining -= unit_sum.total
        else:
            exceeded = True
    if exceeded:
        expense.is_over_limit = True
