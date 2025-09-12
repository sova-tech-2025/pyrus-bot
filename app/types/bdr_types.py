from pydantic import BaseModel

from app.domains.account import AccountTask
from app.domains.bdr import BdrTask
from app.domains.cash import CashTask
from app.domains.payment import PaymentTask


class BdrComposition(BaseModel):
    bdr: BdrTask
    task: AccountTask | CashTask | PaymentTask

    model_config = dict(arbitrary_types_allowed=True)