from app.config.forms import TestFormStatus
from app.domains.account import AccountTask
from app.domains.bdr import BdrTask
from app.domains.cash import CashTask
from app.domains.payment import PaymentTask
from app.types.bdr_types import BdrComposition
from app.shared.pyrus.pyrus import (
    get_form_by_id, set_field_comment_BDR, set_field_comment_counts,
)


def associate_accounts(ctx, bdrs: list[BdrTask]) -> list[BdrComposition]:
    data: list[BdrComposition] = [] # Список ассоциаций счетов к бюджету БДР
    accounts: list[AccountTask] = [] # Список задач счетов

    # Получение задач счетов
    for task in get_form_by_id(ctx, TestFormStatus.ACCOUNTS.value):
        accounts.append(AccountTask(task))

    # Создание списка ассоциаций счетов к бюджету БДР
    for account in accounts:
        for bdr in bdrs:
            if (set(account.extending_article) & set(bdr.extending_article)) and \
                    ''.join(account.units) == ''.join(bdr.units) and \
                    bdr.date_from <= account.date <= bdr.date_to:
                data.append(BdrComposition(bdr=bdr, task=account))
                break

    return data

def associate_cashes(ctx, bdrs: list[BdrTask]) -> list[BdrComposition]:
    data: list[BdrComposition] = [] # Список ассоциаций наличных к бюджету БДР
    cashes: list[CashTask] = [] # Список задач счетов

    # Получение задач счетов
    for task in get_form_by_id(ctx, TestFormStatus.CASH.value):
        cashes.append(CashTask(task))

    # Создание списка ассоциаций наличных к бюджету БДР
    for cash in cashes:
        for bdr in bdrs:
            if (set(cash.extending_article) & set(bdr.extending_article)) and \
                    ''.join(cash.units) == ''.join(bdr.units) and \
                    bdr.date_from <= cash.date <= bdr.date_to:
                data.append(BdrComposition(bdr=bdr, task=cash))
                break

    return data

def associate_payments(ctx, bdrs: list[BdrTask]) -> list[BdrComposition]:
    data: list[BdrComposition] = [] # Список ассоциаций платежей к бюджету БДР
    payments: list[PaymentTask] = [] # Список задач счетов

    # Получение задач счетов
    for task in get_form_by_id(ctx, TestFormStatus.PAYMENTS.value):
        payments.append(PaymentTask(task))

    # Создание списка ассоциаций наличных к бюджету БДР
    for payment in payments:
        for bdr in bdrs:
            for unit_sum in payment.unit_sums:
                if (set(payment.extending_article) & set(bdr.extending_article)) and \
                        ''.join(unit_sum.unit) == ''.join(bdr.units) and \
                        bdr.date_from <= payment.date <= bdr.date_to:
                    data.append(BdrComposition(bdr=bdr, task=payment))
                    break
    return data

def process_limit(ctx, bdr_compositions: list[BdrComposition]):
    for bdr_composition in bdr_compositions: # Счета
        if isinstance(bdr_composition.task, AccountTask):
            # Уменьшение лимита если задача не превышает его.
            # Проставляем is_over_limit, если задача превышает лимит
            if bdr_composition.bdr.limit >= bdr_composition.task.total:
                bdr_composition.bdr.limit -= bdr_composition.task.total
                bdr_composition.task.is_over_limit = False
            else:
                bdr_composition.task.is_over_limit = True

            # Обновляем превышение лимита
            try:
                set_field_comment_counts(ctx, bdr_composition.task.id, {
                                "text": "",
                                "field_updates": [
                                    {
                                        "id": 28,
                                        "value": "checked" if bdr_composition.task.is_over_limit else "unchecked"
                                    }
                                ]
                })
            except AttributeError as e:
                print(f"Error: {e}")

        elif isinstance(bdr_composition.task, CashTask): # Наличные КЕКС
            # Уменьшение лимита если задача не превышает его.
            # Проставляем is_over_limit, если задача превышает лимит
            if bdr_composition.bdr.limit >= bdr_composition.task.total:
                bdr_composition.bdr.limit -= bdr_composition.task.total
                bdr_composition.task.is_over_limit = False
            else:
                bdr_composition.task.is_over_limit = True

            # Обновляем превышение лимита
            try:
                set_field_comment_counts(ctx, bdr_composition.task.id, {
                    "text": "",
                    "field_updates": [
                        {
                            "id": 15,
                            "value": "checked" if bdr_composition.task.is_over_limit else "unchecked"
                        }
                    ]
                })
            except AttributeError as e:
                print(f"Error: {e}")

        elif isinstance(bdr_composition.task, PaymentTask): # Платежи 2 и более ЮЛ
            payment = bdr_composition.task
            bdr = bdr_composition.bdr
            payment.unit_sums.sort(key=lambda item: item.total, reverse=True)
            print(payment.unit_sums)
            flag = False
            for unit_sum in payment.unit_sums:
                if (set(payment.extending_article) & set(bdr.extending_article)) and \
                        ''.join(unit_sum.unit) == ''.join(bdr.units) and \
                        bdr.date_from <= payment.date <= bdr.date_to:
                    if bdr.limit >= unit_sum.total:
                        bdr.limit -= unit_sum.total
                    else:
                        flag = True
            if flag:
                payment.is_over_limit = True

            # Обновляем превышение лимита
            try:
                set_field_comment_counts(ctx, payment.id, {
                    "text": "",
                    "field_updates": [
                        {
                            "id": 20,
                            "value": "checked" if payment.is_over_limit else "unchecked"
                        }
                    ]
                })
            except AttributeError as e:
                print(f"Error: {e}")

    for bdr_composition in bdr_compositions:
        set_field_comment_BDR(ctx, bdr_composition.bdr.id, {
            "text": "",
            "field_updates": [
                {
                    "id": 6,
                    "value": bdr_composition.bdr.limit,
                }
            ]
        })