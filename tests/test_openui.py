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


def _saved(rows):
    return {"columns": [{"name": name} for name in ("asset", "value", "time", "stopped", "lat", "lon")], "rows": rows}


@pytest.mark.parametrize("kind,mapping,rows", [
    ("bar", {"category": "asset", "value": "value"}, [{"asset": "A", "value": 0}]),
    ("line", {"x": "time", "series": ["value"], "inactive": "stopped"}, [{"time": "2026-10-17", "value": None, "stopped": 1}]),
    ("map", {"lat": "lat", "lon": "lon", "label": "asset"}, [{"asset": "A", "lat": 32.1, "lon": -102.1}]),
    ("heatmap", {"x": "time", "y": "asset", "value": "value"}, [{"asset": "A", "time": "2026-10", "value": 0}]),
])
def test_all_new_view_types_use_saved_columns_and_keep_zero_or_null(kind, mapping, rows):
    from app.openui import validate_view_data
    validate_view_data({"type": kind, "mapping": mapping}, _saved(rows))


@pytest.mark.parametrize("kind,mapping,rows", [
    ("bar", {"category": "asset", "value": "value"}, [{"value": "7"}]),
    ("bar", {"category": "asset", "value": "value"}, [{"value": float("inf")}]),
    ("bar", {"category": "asset", "value": "value"}, [{"value": True}]),
    ("line", {"x": "time", "series": ["value"], "inactive": "stopped"}, [{"value": 3, "stopped": "yes"}]),
    ("map", {"lat": "lat", "lon": "lon", "label": "asset"}, [{"lat": 91, "lon": 10}]),
    ("map", {"lat": "lat", "lon": "lon", "label": "asset"}, [{"lat": 30, "lon": -181}]),
    ("heatmap", {"x": "time", "y": "asset", "value": "value"}, [{"time": "Oct", "asset": "A", "value": 0}, {"time": "Oct", "asset": "A", "value": 1}]),
    ("line", {"x": "time", "series": ["invented"]}, []),
])
def test_new_views_reject_untrusted_types_ranges_columns_and_duplicate_cells(kind, mapping, rows):
    from app.openui import validate_view_data
    with pytest.raises(ValueError):
        validate_view_data({"type": kind, "mapping": mapping}, _saved(rows))
