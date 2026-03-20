from app.config.forms import FormStatus
from app.domains.bdr import BdrTask
from app.service.bdr import (
    associate_accounts,
    associate_cashes,
    associate_new_cashes,
    associate_new_payments,
    process_limit,
    associate_payments,
)
from app.shared.pyrus.pyrus import auth, get_form_by_id, set_field_comment_BDR
from app.types.bdr_types import BdrComposition


def _get_ctx():
    from app import main

    return main.ctx


def budget_count():
    ctx = _get_ctx()

    bdrs: list[BdrTask] = []
    for task in get_form_by_id(ctx, FormStatus.BDR.value):
        bdrs.append(BdrTask(task))

    bdr_tasks: list[BdrComposition] = []

    bdr_tasks.extend(associate_accounts(ctx, bdrs))
    bdr_tasks.extend(associate_cashes(ctx, bdrs))
    bdr_tasks.extend(associate_payments(ctx, bdrs))
    bdr_tasks.extend(associate_new_cashes(ctx, bdrs))
    bdr_tasks.extend(associate_payments(ctx, bdrs))
    bdr_tasks.extend(associate_new_payments(ctx, bdrs))

    bdr_tasks.sort(key=lambda item: item.task.create_date)

    process_limit(ctx, bdr_tasks)


def set_all_limits():
    ctx = _get_ctx()

    bdrs: list[BdrTask] = []

    for task in get_form_by_id(ctx, FormStatus.BDR.value):
        bdrs.append(BdrTask(task))

    for bdr in bdrs:
        set_field_comment_BDR(
            ctx,
            bdr.id,
            {
                "text": "",
                "field_updates": [
                    {
                        "id": bdr.limit_id,
                        "value": bdr.limit,
                    }
                ],
            },
        )


def authenticate():
    ctx = _get_ctx()
    access_token = auth()
    ctx["access_token"] = access_token
