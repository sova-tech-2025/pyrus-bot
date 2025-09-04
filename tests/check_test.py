import json
import pytest
from unittest.mock import patch, MagicMock
from app.service.check import handle_form_mutation

def test_handle_form_mutation_selects_bdr_correctly():
    ctx = MagicMock()

    task = None
    fake_bdr = None

    with open("counts_task.json", "r", encoding="utf-8") as f:
        task = json.load(f)
    with open("bdr_tasks.json", "r", encoding="utf-8") as f:
        fake_bdr = json.load(f)


    with patch("app.service.check.get_form_budget_BDR", return_value=fake_bdr) as mock_get_bdr, \
            patch("app.service.check.set_field_comment_BDR", return_value={}) as mock_set_bdr, \
            patch("app.service.check.set_field_comment_counts", return_value={}) as mock_set_counts:

        handle_form_mutation(task, ctx)

        mock_get_bdr.assert_called_once_with(ctx)

