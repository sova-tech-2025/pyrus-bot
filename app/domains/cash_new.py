import os
from datetime import datetime


class CashNewTask:
    id: int
    create_date: datetime
    extending_article: list[str] | None
    units: list[str]
    date: str
    total: float
    is_over_limit: bool

    OVERLIMIT_ID = os.getenv("CASH_NEW_OVERLIMIT_ID")
    # OVERLIMIT_ID = 14 prod
    # OVERLIMIT_ID = 14 dev

    def __init__(self, task):
        fields = task.get("fields")

        self.id = task.get("id")
        self.create_date = datetime.fromisoformat(
            task.get("create_date").replace("Z", "+00:00")
        )
        self.is_over_limit = False

        # { DEV
        #   "id": 14,
        #   "type": "checkmark",
        #   "name": "Превышение лимита",
        #   "tooltip": "",
        #   "value": "unchecked"
        # }
        # { PROD
        #     "id": 14,
        #     "type": "checkmark",
        #     "name": "Превышение лимита",
        #     "tooltip": "",
        #     "value": "unchecked"
        # }

        for field in fields:
            if field["name"] == "Дата расхода":
                self.date = field.get("value")
            elif field["name"] == "Подразделение":
                self.units = (
                    field.get("value").get("values")
                    if field.get("value") is not None
                    else None
                )
            elif field["name"] == "Статья расходов":
                self.extending_article = (
                    field.get("value").get("values")
                    if field.get("value") is not None
                    else None
                )
            elif field["name"] == "Сумма":
                self.total = field.get("value")
        if not self.date:
            self.date = "1900-01-01"
