from datetime import datetime


class CashTask:
    id: int
    create_date: datetime
    extending_article: list[str] | None
    units: list[str]
    date: str
    total: int
    is_over_limit: bool

    def __init__(self, task):
        fields = task.get("fields")

        self.id = task.get("id")
        self.create_date = datetime.fromisoformat(task.get("create_date").replace("Z", "+00:00"))
        self.is_over_limit = False

        # {
        #   "id": 15,
        #   "type": "checkmark",
        #   "name": "Превышение лимита",
        #   "tooltip": "",
        #   "value": "unchecked"
        # }

        for field in fields:
            if field['name'] == "Дата расхода":
                self.date = field.get("value")
            elif field['name'] == "Подразделение":
                self.units = field.get("value").get("values")
            elif field['name'] == "Статья расходов":
                self.extending_article = field.get("value").get("values")
            elif field['name'] == "Сумма":
                self.total = field.get("value")
