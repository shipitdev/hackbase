"""One opt-in, real-provider Q1 check against a private snapshot of shared data."""
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.errors import AppError
from app.main import create_app
from app.provider import CompatibleProvider
from app.store import KnowledgeStore

ROOT = Path(__file__).resolve().parents[1]
QUESTION = "Is WELL-0001 currently producing? Show a status card and explain the latest inspection, the temperature rule, and any relevant planned shut-in note. Cite the evidence."


def _snapshot(source, target):
    """Use SQLite backup so the live shared database is never opened for writes."""
    source_db = sqlite3.connect(f"file:{Path(source).resolve()}?mode=ro", uri=True)
    target_db = sqlite3.connect(target)
    try:
        source_db.backup(target_db)
    finally:
        target_db.close()
        source_db.close()


def _check_answer(answer, expected):
    if answer.get("status") != "complete":
        raise ValueError("API returned no complete answer")
    if answer.get("analysis_date") != "2026-10-17":
        raise ValueError("API used an unexpected analysis date")
    prose = answer.get("answer", "").lower()
    if expected.get("producing") and "producing" not in prose:
        raise ValueError("Answer text does not state the independently checked production state")
    if not expected.get("producing") and not any(term in prose for term in ("not producing", "not currently producing", "isn't producing", "not in production")):
        raise ValueError("Answer text does not state the independently checked production state")
    cards = [c for c in answer.get("components", []) if c.get("type") == "card"]
    cards = [c for c in cards if {"asset_id", "producing"} <= set(c.get("mapping", {}).get("fields", []))]
    if not cards:
        raise ValueError("Answer did not return a status card with the well and production state")
    card = cards[0]
    rows = card.get("data", {}).get("rows", [])
    if len(rows) != 1 or any(rows[0].get(k) != expected.get(k) for k in ("asset_id", "producing")):
        raise ValueError("Status card does not match the independently queried latest inspection")
    if any(k in rows[0] and rows[0][k] != expected[k] for k in ("inspection_id", "inspected_at")):
        raise ValueError("Status card uses a different inspection")
    citations = {c.get("id") for c in answer.get("citations", [])}
    required = {expected["inspection_id"], "OM-T200#9.3", "CTX-0001-003"}
    if not required <= citations:
        raise ValueError("Answer is missing a required inspection, manual, or planned-shut-in citation")
    result_id = card.get("result_id")
    if not result_id or result_id not in citations:
        raise ValueError("Status card is not backed by a retained query result")
    if card["data"].get("complete") is not True or card["data"].get("truncated"):
        raise ValueError("Status card query result is incomplete")
    return {"state": "producing" if expected["producing"] else "not producing", "inspection_id": expected["inspection_id"], "result_id": result_id, "citations": sorted(required)}


def run(database=ROOT / "data" / "knowledge.sqlite", provider=None):
    database = Path(database)
    if not database.is_file():
        raise AppError("not_ready", f"Shared database not found. Load it with: python3 -m app.load dataset/sample-data --db {database}", 503)
    with tempfile.TemporaryDirectory(prefix="asset-copilot-q1-") as temp:
        temp = Path(temp)
        snapshot, memory_path = temp / "knowledge.sqlite", temp / "memory.sqlite"
        _snapshot(database, snapshot)
        knowledge = KnowledgeStore(snapshot, analysis_date="2026-10-17")
        latest = knowledge.query_shared(
            "SELECT asset_id, inspection_id, inspected_at, producing, wellhead_temp_c, ambient_temp_c "
            "FROM latest_inspections WHERE asset_id=?", ["WELL-0001"]
        )["rows"]
        if len(latest) != 1:
            raise ValueError("Could not independently resolve one latest WELL-0001 inspection")
        expected = latest[0]
        if provider is None:
            load_dotenv(ROOT / ".env", override=False, interpolate=False)
            provider = CompatibleProvider()
        if not provider.configured:
            raise AppError("provider_error", "No provider key is configured", 503)
        app = create_app(knowledge=knowledge, memory_path=memory_path, provider=provider, analysis_date="2026-10-17")
        with TestClient(app) as client:
            users = client.get("/api/users")
            if users.status_code != 200 or not users.json().get("users"):
                raise ValueError("API did not load dataset users")
            user_id = users.json()["users"][0]["user_id"]
            thread = client.post("/api/threads", json={"user_id": user_id})
            if thread.status_code != 201:
                raise ValueError("API could not create a temporary private thread")
            thread_id = thread.json()["thread_id"]
            response = client.post("/api/chat", json={
                "request_id": "live-q1-check", "user_id": user_id,
                "thread_id": thread_id, "text": QUESTION,
            })
            if response.status_code != 200:
                payload = response.json()
                error = payload.get("error", {})
                code = error.get("code", "http_error")
                message = error.get("message", "The backend question request failed")
                raise AppError(code, message, response.status_code)
            answer = response.json()
            checked = _check_answer(answer, expected)
            for component in answer.get("components", []):
                result_id = component.get("result_id")
                stored = client.get(f"/api/results/{result_id}", params={"user_id": user_id})
                if stored.status_code != 200 or stored.json().get("rows", []) != component["data"]["rows"]:
                    raise ValueError("Saved query result does not match the displayed card")
            return {
                "status": "pass", **checked, "analysis_date": answer["analysis_date"],
                "model": answer.get("model"), "served_models": answer.get("served_models", []),
                "usage": answer.get("usage", {}),
            }


if __name__ == "__main__":
    try:
        if sys.argv[1:]:
            raise AppError("invalid_request", "Usage: python3 scripts/check_backend_question.py")
        print(json.dumps(run(), sort_keys=True))
    except AppError as exc:
        print(f"Live question check failed: {exc.code}: {exc.message}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"Live question check failed: {type(exc).__name__}", file=sys.stderr)
        raise SystemExit(1)
