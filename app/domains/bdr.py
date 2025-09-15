class BdrTask:
    id: int
    extending_article: list[str]
    units: list[str]
    date_from: str
    date_to: str
    budget: int
    limit: int | None

    def __init__(self, task, limit=False):
        fields = task.get("fields")
        self.id = task.get("id")
        self.limit = 0

        for field in fields:
            if field["name"] == "Статья расходов":
                self.extending_article = field.get("value").get("values") if field.get("value") is not None else None
            elif field["name"] == "Подразделения 1С":
                self.units = field.get("value").get("values") if field.get("value") is not None else None
            elif field["name"] == "От":
                self.date_from = field.get("value")
            elif field["name"] == "До":
                self.date_to = field.get("value")
            elif field["name"] == "Бюджет":
                self.budget = field.get("value")
            elif field["name"] == "Остаток":
                self.limit = field.get("value")
        if not limit:
            self.limit = self.budget
        elif self.limit == 0 or self.limit is None:
            self.limit = self.budget
