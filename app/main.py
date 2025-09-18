import hashlib
import hmac
import json
import os

from contextlib import asynccontextmanager
from typing import Annotated

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request

from app.config.forms import FormStatus
from app.shared.cron.jobs import authenticate, budget_count
from app.shared.webhook.handler import handle_form_update

load_dotenv()

scheduler = AsyncIOScheduler()

# env
SECRET_KEY = os.getenv("BOT_SECRET_KEY")

ctx = {"access_token": ""}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    scheduler.add_job(budget_count, CronTrigger(minute=0))
    scheduler.add_job(authenticate, CronTrigger(hour="*/12"))
    scheduler.start()
    print("Scheduler started")
    authenticate()
    budget_count()

    yield

    # shutdown
    scheduler.shutdown()
    print("Scheduler stopped")

app = FastAPI(lifespan=lifespan)

@app.post("/")
async def index(request: Request, x_pyrus_sig: Annotated[str, Header()] = ...):
    body = await request.body()
    secret = SECRET_KEY.encode()

    if not _is_signature_correct(body, secret, x_pyrus_sig):
        raise HTTPException(status_code=400, detail="Invalid signature")

    return _prepare_response(body.decode("utf-8"))


def _is_signature_correct(message: bytes, secret: bytes, signature: str) -> bool:
    digest = hmac.new(secret, msg=message, digestmod=hashlib.sha1).hexdigest()
    return hmac.compare_digest(digest, signature.lower())


def _prepare_response(body: str):
    data = json.loads(body)
    task = data.get("task", {})
    print(data)
    if (json.loads(body).get("event") == "comment"
            and task.get("form_id") in [
                FormStatus.PAYMENTS.value,
                FormStatus.CASH.value,
                FormStatus.ACCOUNTS.value
            ] and task.get("current_step") == 1):
        is_over_limit = handle_form_update(next((k.name for k in FormStatus if k.value == task.get("form_id")), None), task)
        if is_over_limit is None:
            return {}
        elif not is_over_limit:
            return {
                "text": "Задача согласована ботом",
                "approval_choice": "approved",
            }
        else:
            return {
                "text": "Задача отклонена ботом",
                "approval_choice": "rejected",
            }

    return {}

@app.get("/")
@app.get("/health")
async def health():
    return {"status": "ok"}
