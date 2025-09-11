from app.config.forms import TestFormStatus
from app.domains.bdr import BdrTask
from app.domains.cash import CashTask
from app.shared.pyrus.pyrus import (
    get_form_by_id,
    set_field_comment_BDR,
    set_field_comment_counts,
)


def process_cash(ctx, bdrs: list[BdrTask]):
    cashes: list[CashTask] = []
    for task in get_form_by_id(ctx, TestFormStatus.CASH.value):
        cashes.append(CashTask(task))

    for cash in cashes:
        for bdr in bdrs:
            if (set(cash.extending_article) & set(bdr.extending_article)) and \
                    ''.join(cash.units) == ''.join(bdr.units) and \
                    bdr.date_from <= cash.date <= bdr.date_to:
                if bdr.limit >= cash.total:
                    bdr.limit -= cash.total
                    cash.is_over_limit = False
                else:
                    cash.is_over_limit = True
                break
        try:
            set_field_comment_counts(ctx, cash.id, {
                            "text": "",
                            "field_updates": [
                                {
                                    "id": 15,
                                    "value": "checked" if cash.is_over_limit else "unchecked"
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
