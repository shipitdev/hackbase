"""Run the official OpenUI parser in the installed frontend package."""
import json
import math
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "frontend/scripts/validate-openui.tsx"
MAX_INPUT = 64_000
MAX_OUTPUT = 16_000


def validate_ui(program, results):
    payload = json.dumps({"program": program, "results": results}, separators=(",", ":"))
    if len(payload) > MAX_INPUT:
        raise ValueError("OpenUI validation input is too large")
    try:
        completed = subprocess.run(
            ["node", "--import", "tsx", str(SCRIPT)],
            input=payload,
            text=True,
            capture_output=True,
            timeout=4,
            cwd=ROOT / "frontend",
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("OpenUI parser is unavailable or timed out") from exc
    if completed.returncode or len(completed.stdout) > MAX_OUTPUT:
        raise ValueError("OpenUI program failed validation")
    try:
        value = json.loads(completed.stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("OpenUI parser returned an invalid response") from exc
    if not isinstance(value, list) or len(value) > 6:
        raise ValueError("OpenUI parser returned invalid views")
    return value


def validate_view_data(view, result):
    """Validate mappings against every saved row before publishing native visuals."""
    required = {
        "card": {"fields"}, "table": {"columns"}, "bar": {"category", "value"},
        "line": {"x", "series"}, "map": {"lat", "lon", "label"},
        "heatmap": {"x", "y", "value"},
    }
    kind, mapping = view.get("type"), view.get("mapping", {})
    if kind not in required or not isinstance(mapping, dict):
        raise ValueError("Unknown visual type or mapping")
    optional = {"line": {"inactive"}, "map": {"details"}}.get(kind, set())
    if not required[kind] <= mapping.keys() or mapping.keys() - (required[kind] | optional):
        raise ValueError("Invalid visual mapping keys")
    columns = {column["name"] for column in result["columns"]}
    for key, value in mapping.items():
        if key in {"fields", "columns", "series", "details"}:
            if not isinstance(value, list) or not value or any(not isinstance(name, str) or name not in columns for name in value):
                raise ValueError("Visual column list does not match its saved result")
        elif not isinstance(value, str) or value not in columns:
            raise ValueError("Visual column does not match its saved result")
    if kind == "card" and len(result["rows"]) != 1:
        raise ValueError("ResultCard needs exactly one saved row")
    numeric_keys = {"bar": ["value"], "line": ["series"], "map": ["lat", "lon"], "heatmap": ["value"]}.get(kind, [])
    for key in numeric_keys:
        names = mapping[key] if isinstance(mapping[key], list) else [mapping[key]]
        for name in names:
            for row in result["rows"]:
                value = row.get(name)
                if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
                    raise ValueError("Chart numeric column must contain finite numbers or null")
    if kind == "line" and mapping.get("inactive"):
        for row in result["rows"]:
            value = row.get(mapping["inactive"])
            if value is not None and (not isinstance(value, (bool, int)) or value not in (0, 1)):
                raise ValueError("Inactive marker must be boolean")
    if kind == "map":
        for row in result["rows"]:
            lat, lon = row.get(mapping["lat"]), row.get(mapping["lon"])
            if (lat is not None and not -90 <= lat <= 90) or (lon is not None and not -180 <= lon <= 180):
                raise ValueError("Map coordinates out of range")
    if kind == "heatmap":
        cells = [(row.get(mapping["x"]), row.get(mapping["y"])) for row in result["rows"]]
        if len(set(cells)) != len(cells):
            raise ValueError("Heatmap needs one saved row per cell; aggregate duplicates in SQL")
