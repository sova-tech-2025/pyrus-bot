from datetime import datetime

class AccountTask:
    id: int
    create_date: datetime
    extending_article: list[str] | None
    article_bdr: list[str] | None
    units: list[str]
    date: str
    total: float
    is_over_limit: bool

    # OVERLIMIT_ID = 57
    OVERLIMIT_ID = 28

    def __init__(self, task):
        fields = task.get("fields")

        self.id = task.get("id")
        self.create_date = datetime.fromisoformat(task.get("create_date").replace("Z", "+00:00"))
        self.is_over_limit = False

        # { DEV
        #     "id": 28,
        #     "type": "checkmark",
        #     "name": "Превышение лимита",
        #     "tooltip": "",
        #     "parent_id": 19,
        #     "value": "unchecked"
        # }
        # { PROD
        #     "id": 57,
        #     "type": "checkmark",
        #     "name": "Превышение лимита",
        #     "tooltip": "",
        #     "value": "unchecked"
        # }

        for field in fields:
            if field['name'] == "Дата счета":
                self.date = field.get("value")
            elif field['name'] == "Подразделение":
                self.units = field.get("value").get("values")
            elif field['name'] == "Статья расходов":
                self.extending_article = field.get("value").get("values") if field.get("value") is not None else None
            elif field['name'] == "Статья БДР":
                self.article_bdr = field.get("value").get("values") if field.get("value") is not None else None
            elif field['name'] == "Сумма":
                self.total = field.get("value")
        if not self.extending_article:
            self.extending_article = self.article_bdr
        if not self.article_bdr and not self.extending_article:
            self.extending_article = ['']
        if not self.date:
            self.date = '1900-01-01'