from datetime import datetime

from app.budget.models import Budget, Expense, ExpenseKind, SplitExpense, UnitSum
from app.budget.rules import budgets_for_recalculation, charge, matching_budgets

NOW = datetime(2025, 1, 1)


def budget(remaining=1000, articles=("A",), units=("U1",)):
    return Budget(
        id=1,
        articles=list(articles),
        units=list(units),
        date_from="2025-01-01",
        date_to="2025-12-31",
        remaining=remaining,
    )


def account(total, articles=("A",), units=("U1",), date="2025-03-01"):
    return Expense(
        kind=ExpenseKind.ACCOUNT,
        id=10,
        create_date=NOW,
        articles=list(articles),
        units=list(units),
        date=date,
        total=total,
    )


def payment(*sums, articles=("A",)):
    return SplitExpense(
        kind=ExpenseKind.PAYMENT,
        id=20,
        create_date=NOW,
        articles=list(articles),
        date="2025-03-01",
        unit_sums=[UnitSum(unit=list(u), total=t) for u, t in sums],
    )


def test_expense_matches_by_article_unit_and_period():
    b = budget()
    assert list(matching_budgets(account(1), [b])) == [b]
    assert list(matching_budgets(account(1, articles=["B"]), [b])) == []
    assert list(matching_budgets(account(1, units=["U2"]), [b])) == []
    assert list(matching_budgets(account(1, date="2026-01-01"), [b])) == []


def test_single_expense_goes_to_first_budget_only():
    b1, b2 = budget(), budget()
    assert budgets_for_recalculation(account(1), [b1, b2]) == [b1]


def test_split_expense_goes_to_every_matching_budget():
    b1, b2 = budget(units=["U1"]), budget(units=["U2"])
    p = payment((["U1"], 5), (["U2"], 5))
    assert budgets_for_recalculation(p, [b1, b2]) == [b1, b2]


def test_charge_within_limit():
    b, e = budget(100), account(100)
    charge(b, e)
    assert b.remaining == 0
    assert e.is_over_limit is False


def test_charge_over_limit_keeps_remaining():
    b, e = budget(50), account(100)
    charge(b, e)
    assert b.remaining == 50
    assert e.is_over_limit is True


def test_split_charges_biggest_sums_first():
    b = budget(100, units=["U1"])
    p = payment((["U1"], 30), (["U1"], 80))
    charge(b, p)
    assert b.remaining == 20  # 80 списали, 30 уже не влезло
    assert p.is_over_limit is True
