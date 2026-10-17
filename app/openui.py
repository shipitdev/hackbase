"""Run the official OpenUI parser in the installed frontend package."""
import json
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
