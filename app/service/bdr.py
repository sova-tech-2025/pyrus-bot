from app.config.forms import TestFormStatus
from app.domains.account import AccountTask
from app.domains.bdr import BdrTask
from app.shared.pyrus.pyrus import (
    get_form_by_id,
    set_field_comment_BDR,
    set_field_comment_counts,
)


def process_limits(ctx, bdrs: list[BdrTask]):
    accounts: list[AccountTask] = []
    for task in get_form_by_id(ctx, TestFormStatus.ACCOUNTS.value):
        accounts.append(AccountTask(task))

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
