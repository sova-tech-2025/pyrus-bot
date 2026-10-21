"""Настройки бота: ID форм Pyrus и переменные окружения."""

import os
from dataclasses import dataclass
from enum import IntEnum

from app.budget.models import ExpenseKind


class FormId(IntEnum):
    """ID форм в Pyrus (прод).

    Dev: ACCOUNTS=2336661, BDR=2346023, PAYMENTS=2346726, CASH=2346729,
    PAYMENTS_NEW=2411266, CASH_NEW=2410908.
    """

    ACCOUNTS = 1216424  # Счета
    BDR = 1320105  # Бюджет БДР
    PAYMENTS = 1254419  # Платежи 2 и более ЮЛ
    CASH = 1177102  # Наличные КЕКС
    PAYMENTS_NEW = 2411266  # Платежи новые
    CASH_NEW = 2410908  # Наличные новые


# Откуда берутся расходы при полном пересчёте бюджета — порядок важен.
# Состав повторяет исходную логику один в один, включая помеченные (!) строки
# (см. «Известные проблемы» в README).
RECALCULATION_SOURCES: tuple[tuple[FormId, ExpenseKind], ...] = (
    (FormId.ACCOUNTS, ExpenseKind.ACCOUNT),
    (FormId.CASH, ExpenseKind.CASH),
    (FormId.PAYMENTS, ExpenseKind.PAYMENT),
    (FormId.CASH, ExpenseKind.CASH_NEW),  # (!) читается старая форма наличных
    (FormId.PAYMENTS, ExpenseKind.PAYMENT),  # (!) платежи учитываются второй раз
    (FormId.PAYMENTS, ExpenseKind.PAYMENT_NEW),  # (!) читается старая форма платежей
)

# Какие формы бот проверяет по вебхуку.
WEBHOOK_FORMS: dict[int, ExpenseKind] = {
    FormId.ACCOUNTS: ExpenseKind.ACCOUNT,
    FormId.PAYMENTS: ExpenseKind.PAYMENT,
    FormId.CASH: ExpenseKind.CASH,
    FormId.PAYMENTS_NEW: ExpenseKind.PAYMENT_NEW,
    FormId.CASH_NEW: ExpenseKind.CASH_NEW,
}


@dataclass(frozen=True)
class Settings:
    bot_login: str | None
    bot_secret_key: str | None
    budget_remaining_field_id: int  # поле «Остаток» в форме БДР
    account_overlimit_field_id: str | None  # «Превышение лимита» в форме «Счета»
    cash_overlimit_field_id: str | None
    payment_overlimit_field_id: str | None
    # Пока не используются: новые формы пишут в поля старых (см. overlimit_field_id).
    cash_new_overlimit_field_id: str | None
    payment_new_overlimit_field_id: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            bot_login=os.getenv("BOT_LOGIN"),
            bot_secret_key=os.getenv("BOT_SECRET_KEY"),
            budget_remaining_field_id=int(os.getenv("BDR_OVERLIMIT_ID") or ""),
            account_overlimit_field_id=os.getenv("ACCOUNT_OVERLIMIT_ID"),
            cash_overlimit_field_id=os.getenv("CASH_OVERLIMIT_ID"),
            payment_overlimit_field_id=os.getenv("PAYMENT_OVERLIMIT_ID"),
            cash_new_overlimit_field_id=os.getenv("CASH_NEW_OVERLIMIT_ID"),
            payment_new_overlimit_field_id=os.getenv("PAYMENT_NEW_OVERLIMIT_ID"),
        )

    @property
    def webhook_secret(self) -> str:
        return self.bot_secret_key or ""

    def overlimit_field_id(self, kind: ExpenseKind) -> str | None:
        """ID чекбокса «Превышение лимита» для расхода данного вида."""
        return {
            ExpenseKind.ACCOUNT: self.account_overlimit_field_id,
            ExpenseKind.CASH: self.cash_overlimit_field_id,
            ExpenseKind.CASH_NEW: self.cash_overlimit_field_id,  # (!) поле старой формы
            ExpenseKind.PAYMENT: self.payment_overlimit_field_id,
            ExpenseKind.PAYMENT_NEW: self.payment_overlimit_field_id,  # (!) то же
        }[kind]
