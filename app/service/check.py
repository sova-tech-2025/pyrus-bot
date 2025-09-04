from app.shared.pyrus import *

def handle_form_mutation(task, ctx):
    key_data = {
        "Подразделение": '',
        "Статья расходов": '',
        "Статья БДР": '',
        "Сумма": '',
    }

    date = None

    for field in task['fields']:
        if field['name'] == "Дата счета":
            date = field.get('value')
        elif field['name'] == "Подразделение":
            key_data["Подразделение"] = field.get('value')
        elif field['name'] == "Статья расходов" and key_data["Статья расходов"] == '':
            key_data["Статья расходов"] = field.get('value')
        elif field['name'] == "Статья БДР":
            key_data["Статья БДР"] = field.get('value')
        elif field['name'] == "Сумма":
            key_data["Сумма"] = field.get('value')

    if key_data["Статья расходов"] == '':
        key_data["Статья расходов"] = key_data["Статья БДР"]

    del key_data["Статья БДР"]

    bdrs = get_form_budget_BDR(ctx)
    if not bdrs:
        raise ValueError(task)

    for bdr in bdrs:
        matched = True

        for field in bdr['fields']:
            match field['id']:
                case 1:
                    # TODO: если статья расходов = статье бдр проверить
                    if set(field['value']['values']) & set(key_data["Статья расходов"]["values"]):
                        continue
                    else:
                        matched = False
                        break
                case 2:
                    if ''.join(field['value']['values']) == ''.join(key_data["Подразделение"]['values']):
                        continue
                    else:
                        matched = False
                        break
                case 3:
                    if field['value'] <= date:
                        continue
                    else:
                        matched = False
                    break
                case 4:
                    if field['value'] >= date:
                        continue
                    else:
                        matched = False
                        break
        if matched:
            budget_item = next((item for item in bdr['fields'] if item["name"] == "Бюджет"), None)
            if key_data["Сумма"] <= budget_item['value']:
                # Проставляем остаток
                set_field_comment_BDR(ctx, bdr["id"], {
                        "text": "Обновлены данные формы",
                        "field_updates": [
                            {
                                "id": 6,
                                "value": budget_item['value'] - key_data["Сумма"],
                            }
                        ]
                })
                # Убираем галочку превышение лимита
                set_field_comment_counts(ctx, task["id"], {
                        "text": "Обновлены данные формы",
                        "field_updates": [
                            {
                                "id": 28,
                                "value": "unchecked"
                            }
                        ]
                })
            else:
                # Проставляем галочку превышение лимита
                set_field_comment_counts(ctx, task["id"], {
                    {
                        "text": "Обновлены данные формы",
                        "field_updates": [
                            {
                                "id": 28,
                                "value": "checked"
                            }
                        ]
                    }
                })

            break