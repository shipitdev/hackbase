"""Resumable, isolated live evaluation of the official 18 backend questions."""
import json
import hashlib
import math
import sqlite3
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "data/evaluations/e1"
ANALYSIS_DATE = "2026-10-17"
USERS = {"Michael": "U-201", "Jessica": "U-202", "Tyler": "U-204", "Jake": "U-102", "Laura": "U-401"}
EXPECTED_MEMORY_ENTITIES = {"Q6": {"WELL-0121", "WELL-0138", "WELL-0107"}}


def step(name, user, text, day="2026-10-17", thread="new", visual=None, requires=()):
    return {"name": name, "user": USERS[user], "text": text, "day": day, "thread": thread, "visual": visual, "requires": list(requires)}


SCENARIOS = {
    **{f"Q{i}": [step(f"Q{i}", "Michael" if i == 6 else "Jessica", text, visual=vis)] for i, text, vis in [
        (1, "Is WELL-0001 producing oil right now? When was it last inspected, and by whom? Show me its status card.", "card"),
        (2, "Which wells in Northeast Block 8 are not producing oil right now, and why? Show them in a table.", "table"),
        (3, "Show a line chart of WELL-0001's wellhead temperature against air temperature for the last 13 weeks, and mark when it was not producing oil.", "line"),
        (4, "How many oil spills has WELL-0001 had in the last 4 years, and how much oil in total? List them in a table.", "table"),
        (5, "How many days was WELL-0001 down in 2025?", None),
        (7, "Show on a map every well in Northeast Block 8 with a real spill in the last 90 days.", "map"),
        (8, "Show a heatmap of 2026 spills by geographic area and month.", "heatmap"),
        (9, "Which rules has WELL-0001 broken in the last 12 months, and what is still open?", "table"),
        (10, "In Southwest Block 24, which spills in the last 90 days were not contained within the SOP time limit?", "table"),
    ]},
}
# Correct Q1–10 use independent first-part users unless the guide specifies Michael for memory.
for q in (1, 2, 3, 4, 5, 7, 8, 9, 10):
    SCENARIOS[f"Q{q}"][0]["user"] = USERS["Jessica"]
SCENARIOS["Q6Q11"] = [
    step("Q6", "Michael", "Which 3 wells in Northeast Block 7 had the most downtime in the last 4 months? Show a bar chart.", "2026-10-16", "day1", "bar"),
    step("Q11", "Michael", "For the three wells we discussed yesterday, what have repairs cost this year?", "2026-10-17", "day2", requires=("Q6",)),
]
SCENARIOS["Q12"] = [
    step("Q12-correct", "Michael", "The 15 Oct reading for WELL-0164 is wrong. The handheld thermal gun used in that inspection was faulty; the field crew re-measured the wellhead at 41.0 °C.", "2026-10-17", "correction"),
    step("Q12-repeat", "Michael", "Which wells in Northeast Block 8 are not producing oil right now, and why? Show them in a table.", "2026-10-17", "correction", "table", requires=("Q12-correct",)),
    step("Q12-new-chat", "Michael", "Which wells in Northeast Block 8 are not producing oil right now?", "2026-10-17", "new", "table", requires=("Q12-correct",)),
]
SCENARIOS["Q13"] = [step("Q13", "Michael", "The AI estimated the 24 Sep spill at WELL-0151 as 4.5 bbl. The field crew measured 5.4 bbl.")]
SCENARIOS["Q14"] = [
    step("Q14-baseline", "Michael", "Which wells in Northeast Block 7 need a root-cause analysis on their pump jack?", "2026-10-17", "rule", "table"),
    step("Q14-rule", "Michael", "Note for all T350 wells: our team now wants a pump jack root-cause analysis after 2 repairs, not 3.", "2026-10-17", "rule"),
    step("Q14-new-chat", "Michael", "Which wells in Northeast Block 7 need a root-cause analysis on their pump jack?", "2026-10-17", "new", "table", requires=("Q14-rule",)),
]
SCENARIOS["Q15"] = [
    step("Q12-correction", "Michael", "The 15 Oct reading for WELL-0164 is wrong. The handheld thermal gun used in that inspection was faulty; the field crew re-measured the wellhead at 41.0 °C.", "2026-10-17", "michael"),
    step("Q13-correction", "Michael", "The AI estimated the 24 Sep spill at WELL-0151 as 4.5 bbl. The field crew measured 5.4 bbl.", "2026-10-17", "michael"),
    step("Q15-Jessica", "Jessica", "Is WELL-0164 producing oil right now?", "2026-10-17", "new", requires=("Q12-correction", "Q13-correction")),
    step("Q15-Laura", "Laura", "Which spills in Northeast Block 8 in the last 90 days needed a report to the regulator?", "2026-10-17", "laura", "table", requires=("Q12-correction", "Q13-correction")),
]
SCENARIOS["Q16"] = [
    step("Q16-share", "Jake", "FYI for everyone: WELL-0007 will be shut in from 17 Oct for a 10-day planned workover.", "2026-10-17", "share"),
    step("Q16-Michael", "Michael", "Is any downtime planned for WELL-0007?", "2026-10-17", "michael", requires=("Q16-share",)),
    step("Q16-Jessica", "Jessica", "For the three wells we discussed yesterday, what have repairs cost this year?", "2026-10-17", "jessica"),
]
SCENARIOS["Q17"] = [
    step("Q17-Michael", "Michael", "WELL-0175 has been shut in for planned work since 14 Oct.", "2026-10-17", "michael"),
    step("Q17-Tyler", "Tyler", "WELL-0175 is running fine.", "2026-10-17", "tyler", requires=("Q17-Michael",)),
    step("Q17-Jake", "Jake", "WELL-0001 is back online since 14 Oct.", "2026-10-17", "jake"),
]
SCENARIOS["Q18"] = [step("Q18", "Jessica", "Was the 20 Aug spill at WELL-0101 real oil?")]


def private_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(mode=0o600, exist_ok=True)
    path.chmod(0o600)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def step_capture_status(status_code, payload):
    """Capture status describes transport/evidence presence, never correctness."""
    if status_code == 200 and payload.get("status") in {"complete", "partial"} and payload.get("answer"):
        return "answer_captured"
    if status_code == 200:
        return "response_without_answer"
    return "http_error_no_answer"


def safe_evaluation_metadata(body):
    source = body.get("evaluation_metadata", body)
    if not isinstance(source, dict):
        return {}
    safe = {}
    models = source.get("served_models")
    if isinstance(models, list) and all(isinstance(model, str) for model in models):
        safe["served_models"] = models
    usage = source.get("usage")
    if isinstance(usage, dict):
        safe["usage"] = {key: value for key, value in usage.items()
                         if isinstance(key, str) and isinstance(value, (int, float))
                         and not isinstance(value, bool) and math.isfinite(value)}
    latency = source.get("latency_ms")
    if isinstance(latency, (int, float)) and not isinstance(latency, bool) and math.isfinite(latency):
        safe["latency_ms"] = latency
    return safe


def may_start_step(state, name):
    """A recorded or ambiguous paid attempt must never be replayed automatically."""
    return name not in state.get("steps", {})


def reconcile_step(state, name):
    """Make a crash between dispatch and response capture visible on resume."""
    step_state = state.get("steps", {}).get(name)
    if step_state and step_state.get("status") == "attempt_pending":
        step_state["status"] = "manual_review"
        step_state["reason"] = "dispatch may have reached the provider; replay is disabled"
    return may_start_step(state, name)


def persisted_setup(folder, name, request_id):
    db = folder / "knowledge.sqlite"
    if db.exists():
        con = sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True)
        try:
            if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='changes'").fetchone():
                if con.execute("SELECT 1 FROM changes WHERE status='accepted' AND request_key LIKE ? LIMIT 1",
                                (f"%{request_id}%",)).fetchone():
                    return True
        except sqlite3.Error:
            pass
        finally:
            con.close()
    path = folder / f"{name}.json"
    if not path.exists():
        return False
    try:
        response = json.loads(path.read_text()).get("response", {})
    except (OSError, json.JSONDecodeError):
        return False
    entities = set(response.get("entity_ids", []))
    expected = EXPECTED_MEMORY_ENTITIES.get(name)
    if expected:
        return entities == expected
    return bool(entities or response.get("results"))


def dependency_gate(folder, state, scenario, names):
    uncertain = False
    unmet = []
    for name in names:
        previous = state.get("steps", {}).get(name, {})
        request_id = previous.get("request_id", f"e1-{scenario}-{name}")
        if persisted_setup(folder, name, request_id):
            continue
        unmet.append(name)
        uncertain |= previous.get("status") in {
            "http_error_no_answer", "http_error", "response_without_answer", "manual_review",
            "attempt_pending", "harness_error", "answer_captured", "response",
        }
    if not unmet:
        return "ready", []
    return ("manual_review" if uncertain else "blocked"), unmet


def thread_key(user_id, alias):
    return f"{user_id}:{alias}"


def qualify_legacy_thread(state, scenario, user_id, alias):
    key = thread_key(user_id, alias)
    owners = {item["user"] for item in SCENARIOS[scenario] if item["thread"] == alias}
    if key not in state["threads"] and alias in state["threads"] and owners == {user_id}:
        state["threads"][key] = state["threads"].pop(alias)
    return key


def conversation_timestamp(day, order):
    base = datetime.fromisoformat(day.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
    return (base + timedelta(seconds=order)).isoformat()


@contextmanager
def scenario_clock(memory_module, timestamp):
    original = memory_module._now
    calls = 0

    def next_timestamp():
        nonlocal calls
        current = (datetime.fromisoformat(timestamp) + timedelta(microseconds=calls)).isoformat()
        calls += 1
        return current

    memory_module._now = next_timestamp
    try:
        yield
    finally:
        memory_module._now = original


def submit_once(client, folder, state, scenario, item, request_id, payload):
    name = item["name"]
    started = time.monotonic()
    state["steps"][name] = {"status": "attempt_pending", "request_id": request_id,
                             "attempt_started_at": datetime.now(timezone.utc).isoformat()}
    private_json(folder / "state.json", state)
    try:
        response = client.post("/api/chat", json=payload)
    except Exception as exc:
        state["steps"][name] = {"status": "manual_review", "request_id": request_id, "error_type": type(exc).__name__}
        private_json(folder / "state.json", state)
        raise
    body = response.json()
    record = {"scenario": scenario, "name": name, "user_id": item["user"],
              "conversation_day": item["day"], "analysis_date": ANALYSIS_DATE, "prompt": item["text"],
              "status_code": response.status_code, "elapsed_seconds": round(time.monotonic() - started, 3),
              "expected_visual": item["visual"], "response": body}
    private_json(folder / f"{name}.json", record)
    metadata = safe_evaluation_metadata(body)
    state["steps"][name] = {"status": step_capture_status(response.status_code, body), "request_id": request_id,
                            "status_code": response.status_code, "served_models": metadata.get("served_models", []),
                            "usage": metadata.get("usage", {}), "latency_ms": metadata.get("latency_ms")}
    private_json(folder / "state.json", state)
    return response


def init_scenario(key):
    folder = OUT / key
    folder.mkdir(parents=True, exist_ok=True)
    folder.chmod(0o700)
    (folder / "memory.sqlite").touch(mode=0o600, exist_ok=True)
    shared = folder / "knowledge.sqlite"
    if not shared.exists():
        src = sqlite3.connect(f"file:{(ROOT / 'data/knowledge.sqlite').resolve()}?mode=ro", uri=True)
        dst = sqlite3.connect(shared)
        try:
            src.backup(dst)
        finally:
            dst.close(); src.close()
        shared.chmod(0o600)
    state_path = folder / "state.json"
    if not state_path.exists():
        source = ROOT / "data/knowledge.sqlite"
        src = sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True)
        try:
            metadata = dict(src.execute("SELECT key,value FROM metadata"))
        except sqlite3.Error:
            metadata = {}
        finally:
            src.close()
        private_json(state_path, {"threads": {}, "steps": {}, "baseline": {
            "source": "active data/knowledge.sqlite snapshot (not assumed pristine original)",
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "snapshot_sha256": hashlib.sha256(shared.read_bytes()).hexdigest(),
            "dataset_version": metadata.get("dataset_version"),
            "knowledge_revision": metadata.get("knowledge_revision"),
            "analysis_date": ANALYSIS_DATE,
        }})
    return folder, json.loads(state_path.read_text())


def run_step(key, folder, state, item):
    from app import memory as memory_module
    from app.main import create_app
    from app.provider import CompatibleProvider
    from app.store import KnowledgeStore

    if not reconcile_step(state, item["name"]):
        return
    load_dotenv(ROOT / ".env", override=False, interpolate=False)
    provider = CompatibleProvider()
    if not provider.configured:
        raise RuntimeError("configured provider is unavailable")
    owner_thread = qualify_legacy_thread(state, key, item["user"], item["thread"])
    if owner_thread not in state["threads"]:
        state["threads"][owner_thread] = None
    item_order = next(i for i, candidate in enumerate(SCENARIOS[key]) if candidate["name"] == item["name"])
    timestamp = conversation_timestamp(item["day"], item_order)
    knowledge = KnowledgeStore(folder / "knowledge.sqlite", analysis_date=ANALYSIS_DATE)
    api = create_app(knowledge=knowledge, memory_path=folder / "memory.sqlite", provider=provider, analysis_date=ANALYSIS_DATE)
    started = time.monotonic()
    with scenario_clock(memory_module, timestamp):
        with TestClient(api) as client:
            thread_id = state["threads"][owner_thread]
            if thread_id is None:
                res = client.post("/api/threads", json={"user_id": item["user"]})
                if res.status_code != 201:
                    raise RuntimeError(f"thread creation HTTP {res.status_code}")
                thread_id = state["threads"][owner_thread] = res.json()["thread_id"]
                private_json(folder / "state.json", state)
            request_id = f"e1-{key}-{item['name']}"
            response = submit_once(client, folder, state, key, item, request_id,
                                   {"request_id": request_id, "user_id": item["user"], "thread_id": thread_id, "text": item["text"]})
            elapsed = round(time.monotonic() - started, 3)
            state["steps"][item["name"]]["elapsed_seconds"] = elapsed
            private_json(folder / "state.json", state)


def main():
    if len(sys.argv) > 1 and sys.argv[1] not in {"--resume", "--run"}:
        raise SystemExit("usage: python scripts/evaluate_questions.py [--run|--resume]")
    OUT.mkdir(parents=True, exist_ok=True)
    OUT.chmod(0o700)
    for key, items in SCENARIOS.items():
        folder, state = init_scenario(key)
        for item in items:
            if not reconcile_step(state, item["name"]):
                continue
            dependency_status, unmet = dependency_gate(folder, state, key, item["requires"])
            if unmet:
                state["steps"][item["name"]] = {"status": dependency_status, "blocked_by": unmet,
                                                  "reason": "required setup is unconfirmed; inspect persisted state before any new paid turn"}
                private_json(folder / "state.json", state)
                continue
            try:
                run_step(key, folder, state, item)
            except Exception as exc:
                # Record one attempt failure; never retry a provider call automatically.
                if item["name"] not in state["steps"]:
                    state["steps"][item["name"]] = {"status": "harness_error", "error_type": type(exc).__name__, "message": str(exc)[:300]}
                    private_json(folder / "state.json", state)
            state = json.loads((folder / "state.json").read_text())
    print(f"Saved {sum(len(x) for x in SCENARIOS.values())} question-turn outcomes under {OUT}")


if __name__ == "__main__":
    main()
