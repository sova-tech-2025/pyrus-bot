class AccountTask:
    id: int
    extending_article: list[str] | None
    article_bdr: str | list[str] | None
    units: list[str]
    date: str
    total: int
    is_over_limit: bool

    def __init__(self, task):
        fields = task.get("fields")

        self.id = task.get("id")
        self.is_over_limit = False

        for field in fields:
            if field['name'] == "Дата счета":
                self.date = field.get("value")
            elif field['name'] == "Подразделение":
                self.units = field.get("value").get("values")
            elif field['name'] == "Статья расходов":
                self.extending_article = field.get("value").get("values")
            elif field['name'] == "Статья БДР":
                self.article_bdr = field.get("visibility_condition").get("values")
            elif field['name'] == "Сумма":
                self.total = field.get("value")
        if not self.extending_article:
            self.extending_article = [self.article_bdr,]
