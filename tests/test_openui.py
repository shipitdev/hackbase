import pytest

from app import openui


RESULTS = {"R1": {"columns": ["asset_id", "producing"], "rows": [{"asset_id": "WELL-0001", "producing": False}]}}
PROGRAM = 'root = AnswerLayout([card])\ncard = ResultCard("R1", "Status", ["asset_id", "producing"])'


def test_official_parser_returns_only_literal_result_descriptors():
    assert openui.validate_ui(PROGRAM, RESULTS) == [
        {"type": "card", "result_id": "R1", "title": "Status", "mapping": {"fields": ["asset_id", "producing"]}}
    ]


@pytest.mark.parametrize("program", [
    'root = AnswerLayout([card])\ncard = ResultCard("R1", "Status", ["missing"])',
    'query = Query("run_sql", {})\nroot = AnswerLayout([card])\ncard = ResultCard("R1", "Status", ["asset_id"])',
    'root = AnswerLayout([card])\ncard = ResultTable("R2", "Status", ["asset_id"])',
])
def test_official_parser_rejects_invalid_or_unavailable_program_data(program):
    with pytest.raises(ValueError, match="failed validation"):
        openui.validate_ui(program, RESULTS)


def test_parser_process_failure_is_safe(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("private diagnostic")

    monkeypatch.setattr(openui.subprocess, "run", fail)
    with pytest.raises(ValueError, match="unavailable or timed out") as error:
        openui.validate_ui(PROGRAM, RESULTS)
    assert "private diagnostic" not in str(error.value)
