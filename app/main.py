"""Local demo API. User selection is explicit; it is not production authentication."""
import logging
import os
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.agent import Copilot
from app.contracts import ChatRequest, ThreadRequest
from app.errors import AppError
from app.memory import MemoryStore
from app.provider import CompatibleProvider

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=False, interpolate=False)


def create_app(*, knowledge=None, knowledge_path=None, memory_path=None, provider=None, analysis_date=None):
    app = FastAPI(title="Asset Intelligence Copilot", version="0.1.0")
    analysis = analysis_date or os.getenv("ANALYSIS_DATE", "2026-10-16")
    date.fromisoformat(analysis)
    data_dir = Path(os.getenv("DATA_DIR", str(ROOT / "data")))
    shared_path = Path(knowledge_path or data_dir / "knowledge.sqlite")
    memory = MemoryStore(memory_path or data_dir / "memory.sqlite")
    model = provider if provider is not None else CompatibleProvider()
    app.state.knowledge = knowledge
    app.state.memory = memory
    app.state.provider = model
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

    def store():
        if app.state.knowledge is None:
            if not shared_path.is_file():
                raise AppError("not_ready", "Load a dataset first: python3 -m app.load dataset/sample-data --db data/knowledge.sqlite", 503)
            from app.store import KnowledgeStore
            app.state.knowledge = KnowledgeStore(shared_path, analysis_date=analysis)
        return app.state.knowledge

    def user(user_id):
        if not any(row["user_id"] == user_id for row in store().users()):
            raise AppError("not_found", "User not found in the active dataset", 404)

    @app.exception_handler(AppError)
    async def app_error(_request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})

    @app.exception_handler(RequestValidationError)
    async def request_error(_request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"error": {"code": "invalid_request", "message": "Request validation failed", "details": [{"location": list(e["loc"]), "message": e["msg"]} for e in exc.errors()]}})

    @app.exception_handler(Exception)
    async def unexpected_error(_request: Request, exc: Exception):
        LOGGER.error("Unhandled backend error: %s", type(exc).__name__)
        return JSONResponse(status_code=500, content={"error": {"code": "internal_error", "message": "Backend operation failed. See the local server log; no completed answer was recorded."}})

    @app.get("/api/health")
    def health():
        try:
            info = store().info()
        except AppError as exc:
            if exc.code != "not_ready":
                raise
            info = {"dataset_version": None, "knowledge_revision": 0, "analysis_date": analysis, "counts": {}}
        ready = info.get("dataset_version") not in {None, "unloaded"}
        return {**info, "ready": ready, "chat_ready": ready and bool(getattr(model, "configured", True)), "model": model.model}

    @app.get("/api/users")
    def users():
        return {"users": store().users()}

    @app.post("/api/threads", status_code=201)
    def new_thread(body: ThreadRequest):
        user(body.user_id)
        return memory.create_thread(body.user_id)

    @app.get("/api/threads")
    def threads(user_id: str = Query(min_length=1, max_length=100)):
        user(user_id)
        return {"threads": memory.list_threads(user_id)}

    @app.get("/api/threads/{thread_id}/messages")
    def messages(thread_id: str, user_id: str = Query(min_length=1, max_length=100)):
        user(user_id)
        return {"messages": memory.messages(user_id, thread_id)}

    @app.get("/api/results/{result_id}")
    def result(result_id: str, user_id: str = Query(min_length=1, max_length=100), offset: int = Query(default=0, ge=0), limit: int = Query(default=1000, ge=1, le=1000)):
        user(user_id)
        saved = memory.get_result(user_id, result_id)
        return {**saved, "rows": saved["rows"][offset:offset+limit], "page": {"offset": offset, "limit": limit, "stored_rows": len(saved["rows"])}}

    @app.get("/api/evidence/{reference:path}")
    def evidence(reference: str, user_id: str = Query(min_length=1, max_length=100)):
        user(user_id)
        return {"evidence": Copilot(store(), memory, model).run_tool("get_evidence", {"refs": [reference]}, {"user_id": user_id, "thread_id": ""}, "")}

    @app.post("/api/chat")
    def chat(body: ChatRequest):
        user(body.user_id)
        cached = memory.start_request(body.user_id, body.thread_id, body.request_id, body.text)
        if cached is not None:
            return cached
        context = {"user_id": body.user_id, "thread_id": body.thread_id, "request_id": body.request_id, "analysis_date": analysis}
        try:
            answer = Copilot(store(), memory, model).answer(context, body.text)
            return memory.finish_request(body.user_id, body.thread_id, body.request_id, answer)
        except Exception:
            memory.fail_request(body.user_id, body.thread_id, body.request_id)
            raise

    return app


app = create_app()
