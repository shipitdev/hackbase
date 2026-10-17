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


class CheckFailure(Exception):
    """A fixed, safe acceptance diagnostic for this harness."""


def _save_diagnostic(path, answer, reason):
    if path is None:
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(mode=0o600, exist_ok=True)
    path.chmod(0o600)
    path.write_text(json.dumps({"failure": reason, "answer": answer}, ensure_ascii=False, indent=2) + "\n")


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
    status = answer.get("status")
    if status not in {"complete", "partial"}:
        raise CheckFailure("answer.status is neither complete nor partial")
    if answer.get("analysis_date") != "2026-10-17":
        raise CheckFailure("answer.analysis_date is not 2026-10-17")
    prose = answer.get("answer", "").lower()
    if expected.get("producing") and "producing" not in prose:
        raise CheckFailure("answer text does not state the independently checked production state")
    if not expected.get("producing") and not any(term in prose for term in ("not producing", "not currently producing", "isn't producing", "not in production")):
        raise CheckFailure("answer text does not state the independently checked production state")
    cards = [c for c in answer.get("components", []) if c.get("type") == "card"]
    cards = [c for c in cards if {"asset_id", "producing"} <= set(c.get("mapping", {}).get("fields", []))]
    if not cards:
        raise CheckFailure("answer.components has no status card containing asset_id and producing")
    card = cards[0]
    rows = card.get("data", {}).get("rows", [])
    if len(rows) != 1 or any(rows[0].get(k) != expected.get(k) for k in (
        "asset_id", "inspection_id", "inspected_at", "wellhead_temp_c",
        "ambient_temp_c", "production_threshold_c", "producing",
    )):
        raise CheckFailure("status card row does not match the independently queried asset_id and producing value")
    if any(k in rows[0] and rows[0][k] != expected[k] for k in ("inspection_id", "inspected_at")):
        raise CheckFailure("status card row names a different inspection or observation time")
    citations = {c.get("id") for c in answer.get("citations", [])}
    required = {expected["inspection_id"], "OM-T200#9.3", "CTX-0001-003"}
    if not required <= citations:
        raise CheckFailure("answer citations omit the latest inspection, OM-T200#9.3, or CTX-0001-003")
    limitation_text = " ".join(answer.get("limitations", [])).lower()
    if any(term in prose + " " + limitation_text for term in ("counterweight", "november 2025", "nov 2025")) and "CTX-0001-002" not in citations:
        raise CheckFailure("answer mentions the counterweight note without citation CTX-0001-002")
    result_id = card.get("result_id")
    if not result_id or result_id not in citations:
        raise CheckFailure("status card result_id is not among the answer citations")
    if card["data"].get("complete") is not True or card["data"].get("truncated"):
        raise CheckFailure("status card query result is incomplete or truncated")
    result_citations = {c.get("id"): c for c in answer.get("citations", []) if c.get("kind") == "query_result"}
    for component in answer.get("components", []):
        saved = result_citations.get(component.get("result_id"), {}).get("content", {})
        if not saved or saved.get("rows") != component.get("data", {}).get("rows") or not saved.get("complete", True) or saved.get("truncated"):
            raise CheckFailure("component rows do not match a complete cited saved query result")
    limitations = limitation_text
    if status == "partial":
        if not limitations.strip():
            raise CheckFailure("partial answer does not explain its limitations")
    elif limitations:
        raise CheckFailure("answer has limitations but status is complete")
    return {"status": "pass_with_limitations" if status == "partial" else "pass", "state": "producing" if expected["producing"] else "not producing", "inspection_id": expected["inspection_id"], "result_id": result_id, "citations": sorted(required), "limitations": answer.get("limitations", [])}


def run(database=ROOT / "data" / "knowledge.sqlite", provider=None, diagnostic_path=None):
    database = Path(database)
    if not database.is_file():
        raise AppError("not_ready", f"Shared database not found. Load it with: python3 -m app.load dataset/sample-data --db {database}", 503)
    with tempfile.TemporaryDirectory(prefix="asset-copilot-q1-") as temp:
        temp = Path(temp)
        snapshot, memory_path = temp / "knowledge.sqlite", temp / "memory.sqlite"
        _snapshot(database, snapshot)
        knowledge = KnowledgeStore(snapshot, analysis_date="2026-10-17")
        latest = knowledge.query_shared(
            "SELECT asset_id, inspection_id, inspected_at, producing, wellhead_temp_c, ambient_temp_c, production_threshold_c "
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
            try:
                checked = _check_answer(answer, expected)
            except CheckFailure as exc:
                _save_diagnostic(diagnostic_path, answer, str(exc))
                raise
            for component in answer.get("components", []):
                result_id = component.get("result_id")
                stored = client.get(f"/api/results/{result_id}", params={"user_id": user_id})
                if stored.status_code != 200 or stored.json().get("rows", []) != component["data"]["rows"]:
                    message = "saved result rows do not match its displayed component"
                    _save_diagnostic(diagnostic_path, answer, message)
                    raise CheckFailure(message)
            _save_diagnostic(diagnostic_path, answer, "accepted")
            return {
                "status": "pass", **checked, "analysis_date": answer["analysis_date"],
                "model": answer.get("model"), "served_models": answer.get("served_models", []),
                "usage": answer.get("usage", {}),
            }


if __name__ == "__main__":
    try:
        if sys.argv[1:]:
            raise AppError("invalid_request", "Usage: python3 scripts/check_backend_question.py")
        print(json.dumps(run(diagnostic_path=ROOT / "data" / "checks" / "q1-live-diagnostic.json"), sort_keys=True))
    except AppError as exc:
        print(f"Live question check failed: {exc.code}: {exc.message}", file=sys.stderr)
        raise SystemExit(1)
    except CheckFailure as exc:
        print(f"Live question check failed: acceptance: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"Live question check failed: {type(exc).__name__}", file=sys.stderr)
        raise SystemExit(1)
