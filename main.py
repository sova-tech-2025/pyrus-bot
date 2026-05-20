import hashlib
import hmac
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Annotated

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request

from app.config.forms import FormStatus
from app.shared.cron.jobs import authenticate, budget_count
from app.shared.webhook.handler import handle_form_update

load_dotenv()
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

# env
SECRET_KEY: str = os.getenv("BOT_SECRET_KEY") or ""

ctx = {"access_token": ""}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    # scheduler.add_job(budget_count, CronTrigger(minute=0))
    # scheduler.add_job(set_all_limits, CronTrigger(minute=30))
    # scheduler.add_job(authenticate, CronTrigger(hour="*/12"))
    # scheduler.start()
    logger.info("Scheduler started")
    authenticate()
    budget_count()

    yield

    # shutdown
    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(lifespan=lifespan)


@app.post("/")
async def index(request: Request, x_pyrus_sig: Annotated[str, Header()] = ...):  # type: ignore
    logger.debug("1111")
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
    logger.debug(f"Incoming body: {data}")
    task = data.get("task", {})
    response = {
        "text": "Ошибка обработки задачи, свяжитесь с администратором бота",
        "approval_choice": "rejected",
    }
    if (
        json.loads(body).get("event") == "comment"
        and task.get("form_id")
        in [
            FormStatus.PAYMENTS.value,
            FormStatus.CASH.value,
            FormStatus.ACCOUNTS.value,
            # FormStatus.CASH_NEW.value,
            # FormStatus.PAYMENTS_NEW.value,
        ]
        and task.get("current_step") == 1
    ):
        is_over_limit = handle_form_update(
            next((k.name for k in FormStatus if k.value == task.get("form_id")), None),
            task,
        )
        if not is_over_limit:
            response = {
                "approval_choice": "approved",
            }
        else:
            response = {
                "approval_choice": "rejected",
            }
    logger.debug(f"Response: {response}")
    return response


@app.get("/")
@app.get("/health")
async def health():
    return {"status": "ok"}
