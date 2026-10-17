"""User-scoped SQLite storage for conversations, results and request retries."""

import json
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.errors import AppError


def _now():
    return datetime.now(timezone.utc).isoformat()


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _ids(values):
    if not isinstance(values, list):
        return []
    return list(dict.fromkeys(str(v) for v in values if isinstance(v, (str, int)) and str(v)))


class MemoryStore:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS threads (
                    thread_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, title TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS threads_owner ON threads(user_id, created_at);
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, thread_id TEXT NOT NULL,
                    role TEXT NOT NULL, text TEXT NOT NULL, created_at TEXT NOT NULL,
                    answer TEXT, entity_ids TEXT NOT NULL,
                    FOREIGN KEY(thread_id) REFERENCES threads(thread_id)
                );
                CREATE INDEX IF NOT EXISTS messages_thread ON messages(thread_id, created_at, message_id);
                CREATE TABLE IF NOT EXISTS results (
                    result_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, thread_id TEXT NOT NULL,
                    payload TEXT NOT NULL, entity_ids TEXT NOT NULL, created_at TEXT NOT NULL,
                    FOREIGN KEY(thread_id) REFERENCES threads(thread_id)
                );
                CREATE INDEX IF NOT EXISTS results_owner ON results(user_id, result_id);
                CREATE TABLE IF NOT EXISTS requests (
                    request_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, thread_id TEXT NOT NULL,
                    text TEXT NOT NULL, status TEXT NOT NULL, cached_answer TEXT,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    FOREIGN KEY(thread_id) REFERENCES threads(thread_id)
                );
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
                    thread_id TEXT NOT NULL, request_id TEXT NOT NULL, tool TEXT NOT NULL,
                    arguments TEXT NOT NULL, outcome TEXT NOT NULL, created_at TEXT NOT NULL
                );
            """)

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    @contextmanager
    def _db(self):
        db = self._connect()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _owned_thread(db, user_id, thread_id):
        row = db.execute("SELECT 1 FROM threads WHERE thread_id=? AND user_id=?", (thread_id, user_id)).fetchone()
        if not row:
            raise AppError("not_found", "Thread not found", 404)

    def create_thread(self, user_id):
        thread = {"thread_id": str(uuid.uuid4()), "user_id": user_id, "title": "New conversation", "created_at": _now()}
        with self._db() as db:
            db.execute("INSERT INTO threads VALUES (?,?,?,?)", tuple(thread.values()))
        return thread

    def list_threads(self, user_id):
        with self._db() as db:
            rows = db.execute("SELECT thread_id,user_id,title,created_at FROM threads WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()
        return [dict(row) for row in rows]

    def get_thread(self, user_id, thread_id):
        with self._db() as db:
            row = db.execute("SELECT thread_id,user_id,title,created_at FROM threads WHERE thread_id=? AND user_id=?", (thread_id, user_id)).fetchone()
        if not row:
            raise AppError("not_found", "Thread not found", 404)
        return dict(row)

    def append_message(self, user_id, thread_id, role, text, *, answer=None, entity_ids=None, created_at=None):
        if role not in {"user", "assistant"}:
            raise AppError("invalid_request", "Role must be user or assistant")
        message = {"message_id": str(uuid.uuid4()), "user_id": user_id, "thread_id": thread_id, "role": role,
                   "text": str(text), "created_at": created_at or _now(), "answer": answer,
                   "entity_ids": _ids(entity_ids)}
        with self._db() as db:
            self._owned_thread(db, user_id, thread_id)
            db.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?,?)", (
                message["message_id"], user_id, thread_id, role, message["text"], message["created_at"],
                _json(answer) if answer is not None else None, _json(message["entity_ids"])))
            db.execute("UPDATE threads SET title=? WHERE thread_id=? AND title='New conversation' AND ?='user'", (message["text"][:80], thread_id, role))
        return message

    def messages(self, user_id, thread_id):
        with self._db() as db:
            self._owned_thread(db, user_id, thread_id)
            rows = db.execute("SELECT message_id,role,text,created_at,answer,entity_ids FROM messages WHERE thread_id=? ORDER BY created_at,message_id", (thread_id,)).fetchall()
        return [{"message_id": r["message_id"], "role": r["role"], "text": r["text"], "created_at": r["created_at"],
                 "answer": json.loads(r["answer"]) if r["answer"] else None, "entity_ids": json.loads(r["entity_ids"])} for r in rows]

    def get_message(self, user_id, message_id):
        with self._db() as db:
            row = db.execute("SELECT message_id,thread_id,role,text,created_at FROM messages WHERE user_id=? AND message_id=?", (user_id, message_id)).fetchone()
        if row is None:
            raise AppError("not_found", "Message not found", 404)
        return {"id": message_id, "kind": "private_message", "title": "Saved conversation", "content": dict(row)}

    def load_context(self, user_id, thread_id, query=""):
        with self._db() as db:
            self._owned_thread(db, user_id, thread_id)
            rows = db.execute("SELECT message_id,thread_id,role,text,created_at,entity_ids FROM messages WHERE user_id=? ORDER BY created_at DESC,message_id DESC", (user_id,)).fetchall()
        recent, used = [], 0
        for r in rows:
            if r["thread_id"] != thread_id:
                continue
            msg = {"message_id": r["message_id"], "role": r["role"], "text": r["text"], "created_at": r["created_at"], "entity_ids": json.loads(r["entity_ids"])}
            size = len(msg["text"])
            if len(recent) >= 12 or used + size > 12000:
                break
            recent.append(msg)
            used += size
        recent.reverse()
        recent_message_ids = {m["message_id"] for m in recent}
        entity_ids, refs = [], []
        for r in rows:
            ids = json.loads(r["entity_ids"])
            for entity_id in ids:
                if entity_id not in entity_ids:
                    entity_ids.append(entity_id)
            if r["message_id"] not in recent_message_ids and ids and len(refs) < 12:
                refs.append({"message_id": r["message_id"], "thread_id": r["thread_id"], "created_at": r["created_at"], "entity_ids": ids, "preview": r["text"][:240]})
        return {"thread_id": thread_id, "query": str(query)[:500], "messages": recent,
                "entity_ids": entity_ids[:200], "references": refs}

    def save_result(self, user_id, thread_id, shared_rows):
        result_id = str(uuid.uuid4())
        if not isinstance(shared_rows, dict) or not isinstance(shared_rows.get("rows"), list):
            raise AppError("invalid_request", "Result must contain rows")
        entity_ids = _ids([
            value
            for row in shared_rows["rows"] if isinstance(row, dict)
            for value in [row.get("well_id") or row.get("asset_id")]
            if isinstance(value, str) and re.fullmatch(r"WELL-[A-Za-z0-9-]+", value)
        ])
        payload = {**shared_rows, "result_id": result_id, "user_id": user_id, "thread_id": thread_id}
        with self._db() as db:
            self._owned_thread(db, user_id, thread_id)
            db.execute("INSERT INTO results VALUES (?,?,?,?,?,?)", (result_id, user_id, thread_id, _json(payload), _json(entity_ids), _now()))
        return payload

    def get_result(self, user_id, result_id):
        with self._db() as db:
            row = db.execute("SELECT payload FROM results WHERE result_id=? AND user_id=?", (result_id, user_id)).fetchone()
        if not row:
            raise AppError("not_found", "Result not found", 404)
        return json.loads(row["payload"])

    def start_request(self, user_id, thread_id, request_id, text):
        now = _now()
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            self._owned_thread(db, user_id, thread_id)
            row = db.execute("SELECT * FROM requests WHERE request_id=?", (request_id,)).fetchone()
            if row:
                if row["user_id"] != user_id:
                    raise AppError("not_found", "Request not found", 404)
                if (row["thread_id"], row["text"]) != (thread_id, text):
                    raise AppError("invalid_request", "Request ID is already bound to different input")
                if row["status"] == "completed":
                    return json.loads(row["cached_answer"])
                if row["status"] == "in_progress":
                    raise AppError("busy", "Request is already in progress", 409)
                active = db.execute("SELECT 1 FROM requests WHERE user_id=? AND thread_id=? AND status='in_progress' LIMIT 1", (user_id, thread_id)).fetchone()
                if active:
                    raise AppError("busy", "Another request is already in progress for this thread", 409)
                db.execute("UPDATE requests SET status='in_progress',updated_at=? WHERE request_id=?", (now, request_id))
            else:
                active = db.execute("SELECT 1 FROM requests WHERE user_id=? AND thread_id=? AND status='in_progress' LIMIT 1", (user_id, thread_id)).fetchone()
                if active:
                    raise AppError("busy", "Another request is already in progress for this thread", 409)
                db.execute("INSERT INTO requests VALUES (?,?,?,?,?,?,?,?)", (request_id, user_id, thread_id, text, "in_progress", None, now, now))
                db.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?,?)", (str(uuid.uuid4()), user_id, thread_id, "user", text, now, None, "[]"))
                db.execute("UPDATE threads SET title=? WHERE thread_id=? AND user_id=? AND title='New conversation'", (text[:80], thread_id, user_id))
        return None

    def finish_request(self, user_id, thread_id, request_id, answer):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM requests WHERE request_id=?", (request_id,)).fetchone()
            if not row or (row["user_id"], row["thread_id"]) != (user_id, thread_id):
                raise AppError("not_found", "Request not found", 404)
            if row["status"] == "completed":
                return json.loads(row["cached_answer"])
            if row["status"] != "in_progress":
                raise AppError("invalid_request", "Request is not in progress")
            msg_id = str(uuid.uuid4())
            saved = dict(answer) if isinstance(answer, dict) else {"answer": str(answer)}
            saved["message_id"] = msg_id
            ids = _ids(saved.get("entity_ids"))
            used_result_ids = _ids(saved.get("result_ids"))
            if saved.get("result_id") and str(saved["result_id"]) not in used_result_ids:
                used_result_ids.append(str(saved["result_id"]))
            for component in saved.get("components", []):
                if isinstance(component, dict) and component.get("result_id"):
                    result_id = str(component["result_id"])
                    if result_id not in used_result_ids:
                        used_result_ids.append(result_id)
            for result_id in used_result_ids:
                result = db.execute("SELECT entity_ids FROM results WHERE result_id=? AND user_id=? AND thread_id=?", (result_id, user_id, thread_id)).fetchone()
                if not result:
                    raise AppError("not_found", "Result not found", 404)
                ids.extend(v for v in json.loads(result["entity_ids"]) if v not in ids)
            db.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?,?)", (msg_id, user_id, thread_id, "assistant", str(saved.get("answer", "")), _now(), _json(saved), _json(ids)))
            db.execute("UPDATE requests SET status='completed',cached_answer=?,updated_at=? WHERE request_id=?", (_json(saved), _now(), request_id))
        return saved

    def fail_request(self, user_id, thread_id, request_id):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT user_id,thread_id,status FROM requests WHERE request_id=?", (request_id,)).fetchone()
            if not row or (row["user_id"], row["thread_id"]) != (user_id, thread_id):
                raise AppError("not_found", "Request not found", 404)
            if row["status"] == "in_progress":
                db.execute("UPDATE requests SET status='failed',updated_at=? WHERE request_id=?", (_now(), request_id))

    def save_trace(self, user_id, thread_id, request_id, tool, arguments, outcome):
        args, result = _json(arguments)[:4000], _json(outcome)[:4000]
        with self._db() as db:
            self._owned_thread(db, user_id, thread_id)
            request = db.execute("SELECT 1 FROM requests WHERE request_id=? AND user_id=? AND thread_id=?", (request_id, user_id, thread_id)).fetchone()
            if not request:
                raise AppError("not_found", "Request not found", 404)
            db.execute("INSERT INTO traces(user_id,thread_id,request_id,tool,arguments,outcome,created_at) VALUES (?,?,?,?,?,?,?)", (user_id, thread_id, request_id, str(tool)[:100], args, result, _now()))
            db.execute("DELETE FROM traces WHERE trace_id NOT IN (SELECT trace_id FROM traces ORDER BY trace_id DESC LIMIT 1000)")
