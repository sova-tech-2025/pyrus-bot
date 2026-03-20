from pydantic import BaseModel

from app.domains.account import AccountTask
from app.domains.bdr import BdrTask
from app.domains.cash import CashTask
from app.domains.cash_new import CashNewTask
from app.domains.payment import PaymentTask
from app.domains.payment_new import PaymentNewTask


class BdrComposition(BaseModel):
    bdr: BdrTask
    task: AccountTask | CashTask | PaymentTask | CashNewTask | PaymentNewTask

    model_config = dict(arbitrary_types_allowed=True)
