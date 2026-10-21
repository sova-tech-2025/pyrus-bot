"""Сборка приложения: FastAPI, расписание задач и зависимости."""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Annotated

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request

from app.budget.service import BudgetService
from app.config import Settings
from app.pyrus.client import PyrusClient
from app.web.webhook import WebhookHandler, is_signature_valid

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def create_app() -> FastAPI:
    load_dotenv()
    configure_logging()

    settings = Settings.from_env()
    pyrus = PyrusClient(settings.bot_login, settings.bot_secret_key)
    budget_service = BudgetService(pyrus, settings)
    webhook = WebhookHandler(budget_service)
    scheduler = AsyncIOScheduler()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        scheduler.add_job(budget_service.recalculate, CronTrigger(minute=0))
        scheduler.add_job(budget_service.reset_remaining, CronTrigger(minute=30))
        scheduler.add_job(pyrus.authenticate, CronTrigger(hour="*/12"))
        scheduler.start()
        logger.info("Scheduler started")

        pyrus.authenticate()
        budget_service.recalculate()
        yield

        scheduler.shutdown()
        logger.info("Scheduler stopped")

    app = FastAPI(lifespan=lifespan)
    app.state.pyrus = pyrus
    app.state.budget_service = budget_service
    app.state.scheduler = scheduler

    # Обработчик синхронно ходит в Pyrus внутри async-функции, поэтому вебхуки
    # обрабатываются строго по одному — так остатки не пересчитываются параллельно.
    @app.post("/")
    async def pyrus_webhook(
        request: Request, x_pyrus_sig: Annotated[str, Header()]
    ) -> dict:
        body = await request.body()
        if not is_signature_valid(body, settings.webhook_secret, x_pyrus_sig):
            raise HTTPException(status_code=400, detail="Invalid signature")
        return webhook.handle(body.decode("utf-8"))

    @app.get("/")
    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    return app
