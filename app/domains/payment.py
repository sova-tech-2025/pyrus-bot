class PaymentTask:
    id: int
    extending_article: list[str] | None
    article_bdr: str | list[str] | None
    units: list[list[str]]
    date: str
    total: list[int]
    is_over_limit: bool

    def __init__(self, task):
        fields = task.get("fields")

        self.id = task.get("id")
        self.is_over_limit = False

        # {
        #     "id": 20,
        #     "type": "checkmark",
        #     "name": "Превышение лимита",
        #     "tooltip": "",
        #     "value": "unchecked"
        # }

        for field in fields:
            if field['name'] == "Дата расхода": # ?
                self.date = field.get("value")
            elif field['name'] == "Статья расходов": # !
                self.extending_article = field.get("value").get("values")
            elif field['name'] == "Статья БДР": # !
                self.article_bdr = field.get("visibility_condition").get("value")
            elif field['name'] == "Суммы по подразделениям":
                for v in field.get("value"):
                    self.units.append(v.get("cells")[0].get("value").get("values")) # !
                    self.total.append(v.get("cells")[1].get("value")) # !
            if not self.extending_article:
                self.extending_article = [self.article_bdr, ]
