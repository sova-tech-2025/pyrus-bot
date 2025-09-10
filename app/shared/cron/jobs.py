import app.main
from app.service.bdr import process_limits
from app.service.cash import process_cash
from app.shared.pyrus.pyrus import auth


def budget_count():
    process_limits()
    process_cash()

def authenticate():
    access_token = auth()
    app.main.ctx["access_token"] = access_token