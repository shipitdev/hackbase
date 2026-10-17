"""Run the released questions once each against an isolated production snapshot."""
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
OUT = ROOT / "data/evaluations/final-release"
SOURCE_DB = ROOT / "data/knowledge.sqlite"
ANALYSIS_DATE = "2027-01-15"
USERS = {
    "Michael": "U-201", "Robert": "U-301", "Laura": "U-401", "Chris": "U-402",
    "Nathan": "U-601", "Olivia": "U-501",
}


def turn(name, user, text, session="new", visual=None):
    return {"name": name, "user_id": USERS[user], "user": user, "text": text,
            "session": session, "visual": visual}


SCENARIOS = {
    "Q1": [turn("Q1", "Michael", "All our wells feed one reservoir. Map the reservoir pressure across the field from the pressure data.", visual="map")],
    "Q2": [turn("Q2", "Robert", "Which well produced the most oil in 2026?")],
    "Q3": [turn("Q3", "Laura", "Since 1 Nov 2026, every time an operator note reports gas at a well, did we get someone out to that well in time under our operating procedures? List every report and whether the response met the deadline.\n\nShow: a table with Well, Area, Reported at (date and time), Response (record ID and time, or none), Hours to response, Deadline, and Met / Missed.", visual="table")],
    "Q4": [turn("Q4", "Chris", "Across all areas, which temporary flowline bypasses are in place right now, and is each one allowed? Also list any bypass, past or present, that stayed in after its approval ran out or was never approved at all.\n\nShow: a table with Well, Area, Bypass in (date), Bypass out (date, or \"still in\"), Approval (memo ID, or none), Approval valid until, and Status (Allowed / Expired / Not approved).", visual="table")],
    "Q5": [turn("Q5", "Michael", "The State Oil & Gas Commission wrote to us in November 2026 about spills. Which of our spills does the letter cover, and on which ones are we not compliant? Show me a table.\n\nShow: a table with Well, Area, Inspection (ID and date), Volume (bbl), Clean-up job, and Compliant? (Yes / No, with the reason).", visual="table")],
    "Q6": [turn("Q6", "Nathan", "Across the whole field, not just my area, for which wells do the latest inspection and the operator notes disagree about whether the well is producing oil? For each one, what is its real status right now, and why?\n\nShow: a table with Well, Area, Latest inspection (ID, date, what it shows), Latest operator note (date, time, what it says), and Status now (Producing oil / Not producing oil, with \"unconfirmed\" where it applies).", visual="table")],
    "Q7": [
        turn("Q7-1", "Robert", "Over the last month the operators have written notes about wells that sound or behave wrong. Which of those wells haven't had a repair since? Rank the 10 most likely to need a repair in the next 90 days, other than a spill clean-up, and quote the notes as evidence.\n\nShow: a ranked table with Rank, Well, Area, Operator-note evidence (date and quote), Other warning signs in the data, and Last repair on the well.", "q7", "table"),
        turn("Q7-2", "Robert", "Which three would you send a crew to first this week, and why?", "q7"),
    ],
    "Q8": [
        turn("Q8-1", "Nathan", "WELL-0333's recalled pump was swapped out yesterday. The work order isn't in the system yet. Please count it as replaced from now on.\n\nIn every turn, say where each fact came from.", "q8a"),
        turn("Q8-2", "Nathan", "Also, just for me: whenever you list wells, sort them by area and then by well ID, and show costs in thousands of dollars.\n\nIn every turn, say where each fact came from.", "q8a"),
        turn("Q8-3", "Robert", "Which recalled pumps are still in the ground right now?\n\nShow a table. In every turn, say where each fact came from.", "q8b", "table"),
        turn("Q8-4", "Olivia", "Nathan told me the recalled pump on WELL-0577 was swapped as well. Take it off the recall list.\n\nIn every turn, say where each fact came from.", "q8c"),
        turn("Q8-5", "Nathan", "Show me the recalled pumps that are still in the ground in my area, and what it cost to install each one.\n\nShow a table. In every turn, say where each fact came from.", "q8d", "table"),
    ],
    "Q9": [
        turn("Q9-1", "Robert", "How many recalled pumps are still in the ground, and in which areas?", "q9"),
        turn("Q9-2", "Robert", "Different topic. Who leads Northwest Production, and how many wells does that team run?", "q9"),
        turn("Q9-3", "Robert", "What does our operations SOP say about cold weather? Name one well that missed the check in December.", "q9"),
        turn("Q9-4", "Robert", "An operator reported a gas smell at WELL-0332 on 3 Dec. What was the H2S reading?", "q9"),
        turn("Q9-5", "Robert", "Back to the pumps from my first question: which of those wells are not producing oil right now, and when was each one last repaired?", "q9"),
        turn("Q9-6", "Robert", "Of all the wells we've talked about today, which one would you deal with first, and why?", "q9"),
    ],
    "Q10": [turn("Q10", "Michael", "When a well stays shut in longer than the repair itself, what are we usually waiting on: parts, crews, contractors or weather? Break it down by area for jobs started in 2026, with the typical number of extra days, and tell me if any area stands out.\n\nShow: a table of reasons by area (share and typical extra days), and a stacked bar chart by area.", visual="table and stacked bar chart")],
    "Q11": [turn("Q11", "Olivia", "Which region of the field consistently runs hotter?")],
}

assert list(SCENARIOS) == [f"Q{i}" for i in range(1, 12)]
assert sum(map(len, SCENARIOS.values())) == 21


def private_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.touch(mode=0o600, exist_ok=True)
    path.chmod(0o600)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def metadata(body):
    value = body.get("evaluation_metadata", body)
    if not isinstance(value, dict):
        return {}
    result = {}
    models, usage, latency = value.get("served_models"), value.get("usage"), value.get("latency_ms")
    if isinstance(models, list) and all(isinstance(x, str) for x in models):
        result["served_models"] = models
    if isinstance(usage, dict):
        result["usage"] = {k: v for k, v in usage.items() if isinstance(k, str) and isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)}
    if isinstance(latency, (int, float)) and not isinstance(latency, bool) and math.isfinite(latency):
        result["latency_ms"] = latency
    return result


def snapshot():
    if not SOURCE_DB.is_file():
        raise RuntimeError("active data/knowledge.sqlite is missing; wait for dataset activation")
    db = sqlite3.connect(f"file:{SOURCE_DB.resolve()}?mode=ro", uri=True)
    try:
        info = dict(db.execute("SELECT key,value FROM metadata"))
        users = {row[0] for row in db.execute("SELECT user_id FROM users")}
    finally:
        db.close()
    if not set(USERS.values()).issubset(users):
        raise RuntimeError("active DB is not the released dataset (required evaluation users are missing)")
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700)
    OUT.chmod(0o700)
    dest = OUT / "knowledge.sqlite"
    state_path = OUT / "state.json"
    if not dest.exists():
        source = sqlite3.connect(f"file:{SOURCE_DB.resolve()}?mode=ro", uri=True)
        target = sqlite3.connect(dest)
        try:
            source.backup(target)
        finally:
            target.close()
            source.close()
        dest.chmod(0o600)
    if not (OUT / "memory.sqlite").exists():
        (OUT / "memory.sqlite").touch(mode=0o600)
    if not state_path.exists():
        digest = hashlib.sha256(dest.read_bytes()).hexdigest()
        private_json(state_path, {"threads": {}, "steps": {}, "baseline": {
            "source_sha256": hashlib.sha256(SOURCE_DB.read_bytes()).hexdigest(),
            "snapshot_sha256": digest, "dataset_version": info.get("dataset_version"),
            "knowledge_revision": info.get("knowledge_revision"), "analysis_date": ANALYSIS_DATE}})
    state = json.loads(state_path.read_text())
    snap = sqlite3.connect(f"file:{dest.resolve()}?mode=ro", uri=True)
    try:
        eval_info = dict(snap.execute("SELECT key,value FROM metadata"))
    finally:
        snap.close()
    if eval_info.get("dataset_version") != state["baseline"].get("dataset_version"):
        raise RuntimeError("isolated evaluation DB dataset version changed; refusing to continue")
    return state


def run_turn(scenario, item, state, ordinal):
    name = item["name"]
    if name in state["steps"]:
        return
    from app import memory as memory_module
    from app.main import create_app
    from app.provider import CompatibleProvider
    from app.store import KnowledgeStore

    load_dotenv(ROOT / ".env", override=False, interpolate=False)
    provider = CompatibleProvider()
    if not provider.configured:
        raise RuntimeError("configured provider is unavailable")
    key = f'{item["user_id"]}:{item["session"]}'
    state["threads"].setdefault(key, None)
    base_time = datetime(2027, 1, 15, tzinfo=timezone.utc) + timedelta(seconds=ordinal)
    original_now = memory_module._now
    clock_calls = 0

    def fixed_now():
        nonlocal clock_calls
        stamp = (base_time + timedelta(microseconds=clock_calls)).isoformat()
        clock_calls += 1
        return stamp

    folder = OUT / scenario
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    folder.chmod(0o700)
    request_id = f"final-{scenario}-{name}"
    state["steps"][name] = {"status": "attempt_pending", "request_id": request_id,
                             "user_id": item["user_id"], "session": item["session"],
                             "attempt_started_at": datetime.now(timezone.utc).isoformat()}
    private_json(OUT / "state.json", state)
    try:
        memory_module._now = fixed_now
        knowledge = KnowledgeStore(OUT / "knowledge.sqlite", analysis_date=ANALYSIS_DATE)
        api = create_app(knowledge=knowledge, memory_path=OUT / "memory.sqlite", provider=provider, analysis_date=ANALYSIS_DATE)
        with TestClient(api) as client:
            thread_id = state["threads"][key]
            if thread_id is None:
                created = client.post("/api/threads", json={"user_id": item["user_id"]})
                if created.status_code != 201:
                    raise RuntimeError(f"thread creation HTTP {created.status_code}")
                thread_id = state["threads"][key] = created.json()["thread_id"]
                private_json(OUT / "state.json", state)
            started = time.monotonic()
            try:
                response = client.post("/api/chat", json={"request_id": request_id, "user_id": item["user_id"], "thread_id": thread_id, "text": item["text"]})
            except Exception as exc:
                private_json(folder / f"{name}.json", {"scenario": scenario, **item, "analysis_date": ANALYSIS_DATE, "error_type": type(exc).__name__, "error": str(exc)[:500]})
                state["steps"][name] = {"status": "manual_review", "request_id": request_id, "error_type": type(exc).__name__}
                private_json(OUT / "state.json", state)
                return
            try:
                body = response.json()
            except ValueError:
                body = {"error": {"code": "invalid_response", "message": "Response was not JSON"}}
            private_json(folder / f"{name}.json", {"scenario": scenario, **item, "analysis_date": ANALYSIS_DATE,
                "status_code": response.status_code, "elapsed_seconds": round(time.monotonic() - started, 3), "response": body})
            meta = metadata(body)
            state["steps"][name] = {"status": "answer_captured" if response.status_code == 200 and body.get("answer") else "http_error_no_answer",
                "request_id": request_id, "user_id": item["user_id"], "session": item["session"],
                "status_code": response.status_code, "served_models": meta.get("served_models", []),
                "usage": meta.get("usage", {}), "latency_ms": meta.get("latency_ms")}
            private_json(OUT / "state.json", state)
    except Exception as exc:
        # Thread setup/config failures happen before chat dispatch; a pending state is retained if dispatch was ambiguous.
        if state["steps"].get(name, {}).get("status") != "attempt_pending":
            state["steps"][name] = {"status": "harness_error", "request_id": request_id, "error_type": type(exc).__name__, "message": str(exc)[:300]}
            private_json(folder / f"{name}.json", {"scenario": scenario, **item, "error_type": type(exc).__name__, "error": str(exc)[:500]})
            private_json(OUT / "state.json", state)
    finally:
        memory_module._now = original_now


def main():
    if len(sys.argv) > 1 and sys.argv[1] not in {"--run", "--resume"}:
        raise SystemExit("usage: python3 scripts/evaluate_final.py [--run|--resume]")
    state = snapshot()
    ordinal = 0
    for scenario, turns in SCENARIOS.items():
        for item in turns:
            ordinal += 1
            run_turn(scenario, item, state, ordinal)
            state = json.loads((OUT / "state.json").read_text())
    print(f"Captured {len(state['steps'])}/{sum(map(len, SCENARIOS.values()))} turns under {OUT}")


if __name__ == "__main__":
    main()
