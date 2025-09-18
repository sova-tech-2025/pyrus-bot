from app.config.forms import FormStatus
import app.main
from app.domains.account import AccountTask
from app.domains.bdr import BdrTask
from app.domains.cash import CashTask
from app.domains.payment import PaymentTask
from app.service.bdr import associate_account, associate_cash, associate_payment, process_limit, process_limit_task
from app.shared.pyrus.pyrus import get_form_by_id


def handle_form_update(key: str | None, input_task):
    if key is None:
        return

    ctx = app.main.ctx

    bdrs: list[BdrTask] = []
    for task in get_form_by_id(ctx, FormStatus.BDR.value):
        bdrs.append(BdrTask(task, limit=True))

    bdr_task = None
    if key == 'ACCOUNTS':
        account = AccountTask(input_task)
        bdr_task = associate_account(bdrs, account)
    elif key == 'PAYMENTS':
        payment = PaymentTask(input_task)
        bdr_task = associate_payment(bdrs, payment)
    elif key == 'CASH':
        cash = CashTask(input_task)
        bdr_task = associate_cash(bdrs, cash)

    is_over_limit = None
    if bdr_task:
        is_over_limit = process_limit_task(ctx, bdr_task)
    return is_over_limit
