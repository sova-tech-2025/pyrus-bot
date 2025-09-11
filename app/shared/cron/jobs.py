import app.main

from app.config.forms import TestFormStatus
from app.domains.bdr import BdrTask
from app.service.bdr import process_limits
from app.service.cash import process_cash
from app.shared.pyrus.pyrus import auth, get_form_by_id


def budget_count():
    ctx = app.main.ctx

    bdrs: list[BdrTask] = []
    for task in get_form_by_id(ctx, TestFormStatus.BDR.value):
        bdrs.append(BdrTask(task))

    process_limits(ctx, bdrs)
    process_cash(ctx, bdrs)

def authenticate():
    access_token = auth()
    app.main.ctx["access_token"] = access_token
