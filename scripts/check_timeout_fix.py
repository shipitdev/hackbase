"""One-shot live checks for the provider timeout fix; no automatic retries."""
import hashlib
import json
import math
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SOURCE_DB = ROOT / "data/knowledge.sqlite"
OUT = ROOT / "data/evaluations/timeout-fix"
ANALYSIS_DATE = "2027-01-15"
CHECKS = [
    {"name": "Q9-2", "user_id": "U-301", "user": "Robert Hayes",
     "text": "Different topic. Who leads Northwest Production, and how many wells does that team run?",
     "visual": None, "expected": {"lead": "Nathan Pierce", "well_count": 150}},
    {"name": "Q4", "user_id": "U-402", "user": "Chris Dalton",
     "text": "Across all areas, which temporary flowline bypasses are in place right now, and is each one allowed? Also list any bypass, past or present, that stayed in after its approval ran out or was never approved at all.\n\nShow: a table with Well, Area, Bypass in (date), Bypass out (date, or \"still in\"), Approval (memo ID, or none), Approval valid until, and Status (Allowed / Expired / Not approved).",
     "visual": "table", "expected": {"required_columns": ["Well", "Area", "Bypass in", "Bypass out", "Approval", "Approval valid until", "Status"]}},
]
assert len(CHECKS) == 2 and CHECKS[0]["user_id"] == "U-301" and CHECKS[1]["user_id"] == "U-402"


def private_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.touch(mode=0o600, exist_ok=True)
    path.chmod(0o600)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def safe_metadata(body):
    source = body.get("evaluation_metadata", body)
    if not isinstance(source, dict):
        return {}
    out = {}
    models, usage, latency = source.get("served_models"), source.get("usage"), source.get("latency_ms")
    if isinstance(models, list) and all(isinstance(value, str) for value in models):
        out["served_models"] = models
    if isinstance(usage, dict):
        out["usage"] = {key: value for key, value in usage.items()
                         if isinstance(key, str) and isinstance(value, (int, float))
                         and not isinstance(value, bool) and math.isfinite(value)}
    if isinstance(latency, (int, float)) and not isinstance(latency, bool) and math.isfinite(latency):
        out["latency_ms"] = latency
    return out


def initialize(check):
    if not SOURCE_DB.is_file():
        raise RuntimeError("active data/knowledge.sqlite is missing")
    source = sqlite3.connect(f"file:{SOURCE_DB.resolve()}?mode=ro", uri=True)
    try:
        info = dict(source.execute("SELECT key,value FROM metadata"))
        users = {row[0] for row in source.execute("SELECT user_id FROM users")}
    finally:
        source.close()
    if check["user_id"] not in users or info.get("dataset_version") is None:
        raise RuntimeError("active DB is not the released final dataset")
    folder = OUT / check["name"]
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    folder.chmod(0o700)
    db_path, memory_path, state_path = folder / "knowledge.sqlite", folder / "memory.sqlite", folder / "state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if state.get("check_name") != check["name"] or state.get("user_id") != check["user_id"]:
            raise RuntimeError(f"existing state identity mismatch for {check['name']}")
    else:
        src = sqlite3.connect(f"file:{SOURCE_DB.resolve()}?mode=ro", uri=True)
        dst = sqlite3.connect(db_path)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()
        db_path.chmod(0o600)
        memory_path.touch(mode=0o600)
        state = {"check_name": check["name"], "user_id": check["user_id"], "attempt": None,
                 "baseline": {"dataset_version": info.get("dataset_version"),
                              "source_sha256": hashlib.sha256(SOURCE_DB.read_bytes()).hexdigest(),
                              "snapshot_sha256": hashlib.sha256(db_path.read_bytes()).hexdigest(),
                              "analysis_date": ANALYSIS_DATE}}
        private_json(state_path, state)
    snapshot = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
    try:
        snap_info = dict(snapshot.execute("SELECT key,value FROM metadata"))
    finally:
        snapshot.close()
    if snap_info.get("dataset_version") != state["baseline"].get("dataset_version"):
        raise RuntimeError(f"isolated snapshot dataset version mismatch for {check['name']}")
    return folder, db_path, memory_path, state


def run_one(check):
    from app import memory as memory_module
    from app.main import create_app
    from app.provider import CompatibleProvider
    from app.store import KnowledgeStore

    folder, db_path, memory_path, state = initialize(check)
    if state.get("attempt") is not None:
        return
    load_dotenv(ROOT / ".env", override=False, interpolate=False)
    provider = CompatibleProvider()
    if not provider.configured:
        raise RuntimeError("configured provider is unavailable")
    knowledge = KnowledgeStore(db_path, analysis_date=ANALYSIS_DATE)
    api = create_app(knowledge=knowledge, memory_path=memory_path, provider=provider, analysis_date=ANALYSIS_DATE)
    stamp = datetime(2027, 1, 15, tzinfo=timezone.utc)
    original_now, calls = memory_module._now, 0

    def fixed_now():
        nonlocal calls
        result = (stamp + timedelta(microseconds=calls)).isoformat()
        calls += 1
        return result

    request_id = f"timeout-fix-{check['name']}"
    attempt = {"status": "attempt_pending", "request_id": request_id,
               "user_id": check["user_id"], "session": check["name"],
               "started_at": datetime.now(timezone.utc).isoformat()}
    state["attempt"] = attempt
    private_json(folder / "state.json", state)
    memory_module._now = fixed_now
    try:
        with TestClient(api) as client:
            thread_response = client.post("/api/threads", json={"user_id": check["user_id"]})
            if thread_response.status_code != 201:
                attempt.update(status="harness_error", status_code=thread_response.status_code)
                private_json(folder / "result.json", {"check": check, "thread_response": thread_response.json()})
                private_json(folder / "state.json", state)
                return
            thread_id = thread_response.json()["thread_id"]
            attempt["thread_id"] = thread_id
            attempt["dispatch_started_at"] = datetime.now(timezone.utc).isoformat()
            private_json(folder / "state.json", state)
            started = time.monotonic()
            try:
                response = client.post("/api/chat", json={"request_id": request_id,
                    "user_id": check["user_id"], "thread_id": thread_id, "text": check["text"]})
            except Exception as exc:
                record = {"check": check, "analysis_date": ANALYSIS_DATE, "thread_id": thread_id,
                          "elapsed_seconds": round(time.monotonic() - started, 3),
                          "error_type": type(exc).__name__, "error": str(exc)[:500]}
                private_json(folder / "result.json", record)
                attempt.update(status="manual_review", error_type=type(exc).__name__)
                private_json(folder / "state.json", state)
                return
            elapsed = round(time.monotonic() - started, 3)
            try:
                body = response.json()
            except ValueError:
                body = {"error": {"code": "invalid_response", "message": "Response was not JSON"}}
            record = {"check": check, "analysis_date": ANALYSIS_DATE, "thread_id": thread_id,
                      "status_code": response.status_code, "elapsed_seconds": elapsed, "response": body}
            private_json(folder / "result.json", record)
            meta = safe_metadata(body)
            attempt.update(status="captured", status_code=response.status_code, elapsed_seconds=elapsed,
                           served_models=meta.get("served_models", []), usage=meta.get("usage", {}),
                           latency_ms=meta.get("latency_ms"))
            private_json(folder / "state.json", state)
    except Exception as exc:
        # A pending attempt may have reached the provider; preserve it to fence off retries.
        if state.get("attempt", {}).get("status") != "attempt_pending":
            state["attempt"] = {"status": "harness_error", "request_id": request_id,
                                "error_type": type(exc).__name__, "message": str(exc)[:300]}
            private_json(folder / "result.json", {"check": check, "error_type": type(exc).__name__, "error": str(exc)[:500]})
            private_json(folder / "state.json", state)
    finally:
        memory_module._now = original_now


def main():
    if len(sys.argv) > 1 and sys.argv[1] not in {"--run", "--resume"}:
        raise SystemExit("usage: python3 scripts/check_timeout_fix.py [--run|--resume]")
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700)
    OUT.chmod(0o700)
    for check in CHECKS:
        run_one(check)
    print(f"Captured {sum((OUT / c['name'] / 'result.json').exists() for c in CHECKS)}/2 checks under {OUT}")


if __name__ == "__main__":
    main()
