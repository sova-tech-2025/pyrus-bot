import app.main

from app.config.forms import TestFormStatus
from app.domains.bdr import BdrTask
from app.service.bdr import associate_accounts, associate_cashes, process_limit, associate_payments
from app.shared.pyrus.pyrus import auth, get_form_by_id
from app.types.bdr_types import BdrComposition


def budget_count():
    ctx = app.main.ctx

    bdrs: list[BdrTask] = []
    for task in get_form_by_id(ctx, TestFormStatus.BDR.value):
        bdrs.append(BdrTask(task))

    bdr_tasks: list[BdrComposition] = []

    bdr_tasks.extend(associate_accounts(ctx, bdrs))
    bdr_tasks.extend(associate_cashes(ctx, bdrs))
    bdr_tasks.extend(associate_payments(ctx, bdrs))

    bdr_tasks.sort(key=lambda item: item.task.create_date)

    process_limit(ctx, bdr_tasks)



def authenticate():
    access_token = auth()
    app.main.ctx["access_token"] = access_token
