from enum import Enum

# class FormStatus(Enum):
# ACCOUNTS = 2336661  # Счета
# BDR = 2346023  # Бюджет БДР
# PAYMENTS = 2346726  # Платежи 2 и более ЮЛ
# CASH = 2346729  # Наличные КЕКС
# PAYMENTS_NEW = 2411266  # Платежи новые
# CASH_NEW = 2410908  # Наличные новые


class FormStatus(Enum):
    ACCOUNTS = 1216424  # Счета
    BDR = 1320105  # Бюджет БДР
    PAYMENTS = 1254419  # Платежи 2 и более ЮЛ
    CASH = 1177102  # Наличные КЕКС
    PAYMENTS_NEW = 2411266  # Платежи новые
    CASH_NEW = 2410908  # Наличные новые
