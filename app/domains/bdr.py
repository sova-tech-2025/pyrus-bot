class BdrTask:
    id: int
    extending_article: list[str]
    units: list[str]
    date_from: str
    date_to: str
    budget: int
    limit: int

    def __init__(self, task):
        fields = task.get("fields")
        self.id = task.get("id")

        for field in fields:
            if field["name"] == "Статья расходов":
                self.extending_article = field.get("value").get("values")
            if field["name"] == "Подразделения 1С":
                self.units = field.get("value").get("values")
            if field["name"] == "От":
                self.date_from = field.get("value")
            if field["name"] == "До":
                self.date_to = field.get("value")
            if field["name"] == "Бюджет":
                self.budget = field.get("value")
        self.limit = self.budget
