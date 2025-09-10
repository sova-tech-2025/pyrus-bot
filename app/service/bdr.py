import app.main
from app.domains.account import AccountTask
from app.domains.bdr import BdrTask
from app.shared.pyrus.pyrus import (
    get_form_accounts,
    get_form_budget_BDR,
    set_field_comment_BDR,
    set_field_comment_counts,
)


def process_limits():
    ctx = app.main.ctx
    accounts: list[AccountTask] = []
    for task in get_form_accounts(ctx):
        accounts.append(AccountTask(task))

    bdrs: list[BdrTask] = []
    for task in get_form_budget_BDR(ctx):
        bdrs.append(BdrTask(task))

    for account in accounts:
        for bdr in bdrs:
            if (set(account.extending_article) & set(bdr.extending_article)) and \
                    ''.join(account.units) == ''.join(bdr.units) and \
                    bdr.date_from <= account.date <= bdr.date_to:
                if bdr.limit >= account.total:
                    bdr.limit -= account.total
                    account.is_over_limit = False
                else:
                    account.is_over_limit = True
                break
        try:
            set_field_comment_counts(ctx, account.id, {
                            "text": "",
                            "field_updates": [
                                {
                                    "id": 28,
                                    "value": "checked" if account.is_over_limit else "unchecked"
                                }
                            ]
            })
        except AttributeError as e:
            print(f"Ошибка: {e}")

    for bdr in bdrs:
        set_field_comment_BDR(ctx, bdr.id, {
            "text": "",
            "field_updates": [
                {
                    "id": 6,
                    "value": bdr.limit,
                }
            ]
        })
