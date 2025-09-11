from enum import Enum


class TestFormStatus(Enum):
    ACCOUNTS = 2336661 # Счета
    BDR = 2346023 # Бюджет БДР
    PAYMENTS = 2346726 # Платежи 2 и более ЮЛ
    CASH = 2346729 # Наличные КЕКС

class _FormStatus(Enum):
    ACCOUNTS = 2336661 # Счета
    BDR = 2346023 # Бюджет БДР
    PAYMENTS = 2346726 # Платежи 2 и более ЮЛ
    CASH = 2346729 # Наличные КЕКС
