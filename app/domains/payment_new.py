from datetime import datetime

from pydantic import BaseModel


class UnitSum(BaseModel):
    unit: list[str]
    total: float


class PaymentNewTask:
    id: int
    create_date: datetime
    extending_article: list[str] | None
    article_bdr: list[str] | None
    unit_sums: list[UnitSum]
    date: str | None
    is_over_limit: bool

    OVERLIMIT_ID = 17
    # OVERLIMIT_ID = 20

    def __init__(self, task):
        fields = task.get("fields") or []

        self.id = task.get("id")
        self.create_date = datetime.fromisoformat(
            task.get("create_date").replace("Z", "+00:00")
        )
        self.is_over_limit = False
        self.unit_sums = []
        self.extending_article = None
        self.article_bdr = None
        self.date = None

        # { DEV
        #     "id": 20,
        #     "type": "checkmark",
        #     "name": "Превышение лимита",
        #     "tooltip": "",
        #     "value": "unchecked"
        # }
        # { PROD
        #     "id": 27,
        #     "type": "checkmark",
        #     "name": "Превышение лимита",
        #     "tooltip": "",
        #     "value": "unchecked"
        # }

        for field in fields:
            if field["name"] == "Дата":
                self.date = field.get("value")
                if self.date is None:
                    self.date = self.create_date.strftime("%Y-%m-%d")
            elif field["name"] == "Статья расходов":
                self.extending_article = (
                    field.get("value").get("values")
                    if field.get("value") is not None
                    else None
                )
            elif field["name"] == "Статья БДР":
                self.article_bdr = (
                    field.get("value").get("values")
                    if field.get("value") is not None
                    else None
                )
            elif field["name"] == "Суммы по подразделениям":
                for v in field.get("value") or []:
                    cells = v.get("cells") or []
                    if len(cells) < 2:
                        continue
                    unit_cell = cells[0].get("value") if cells[0] else None
                    total_cell = cells[1].get("value") if cells[1] else None
                    unit_values = (
                        unit_cell.get("values") if isinstance(unit_cell, dict) else None
                    )
                    if unit_values is None or total_cell is None:
                        continue
                    self.unit_sums.append(
                        UnitSum(
                            unit=unit_values,
                            total=total_cell,
                        )
                    )
            if not self.extending_article:
                self.extending_article = self.article_bdr
            if not self.article_bdr and not self.extending_article:
                self.extending_article = [""]
            if not self.date:
                self.date = "1900-01-01"
