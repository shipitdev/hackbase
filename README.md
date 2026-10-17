# Asset Intelligence Copilot backend

Python/FastAPI backend for the FlytBase asset-intelligence challenge. It loads the real sample data, runs restricted analytics tools, keeps shared corrections separate from private chats, and returns source-backed answers with generated component descriptions. The frontend is a later phase.

## Run locally

Use Python 3.11+ and install the dependencies in a virtual environment:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m app.load dataset/sample-data --db data/knowledge.sqlite
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open [API documentation](http://127.0.0.1:8000/docs) or `/api/health`. Loading the dataset does not need a model key. The server reports `ready` for data availability and `chat_ready` separately for provider configuration.

If the dataset is absent, obtain the [official dataset repository](https://github.com/FlytBaseAILabs/flytbase-ahc-swe-asset-intelligence-dataset) locally and point the loader at its `sample-data` directory.

## Runtime model

Set these environment variables **before starting the server**. `.env.example` lists the settings; `.env` files are not read automatically.

```sh
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_MODEL=google/gemma-4-26b-a4b-it:free
# Set LLM_API_KEY securely in your shell, then start uvicorn.
```

`OPENROUTER_API_KEY` is also accepted. OpenRouter currently lists this [Gemma free model](https://openrouter.ai/google/gemma-4-26b-a4b-it:free) with tool support; availability and account limits can change. A free endpoint still requires an account/key. No paid fallback is selected automatically.

For local Ollama, set `LLM_BASE_URL=http://127.0.0.1:11434/v1` and `LLM_MODEL` to an installed tool-capable model; no key is required for loopback providers. The adapter uses OpenAI-compatible **Chat Completions**. This is not a Responses API adapter; choose a model/provider supporting tool calls on that endpoint. OpenCode editor access alone does not configure backend model access.

The backend returns an explicit provider error when credentials are missing. It does not substitute canned answers. Automated tests use a scripted model/HTTP transport for repeatability; they do not demonstrate live model answer quality.

## API flow

1. `GET /api/users` → select a dataset user ID.
2. `POST /api/threads` with `{"user_id":"U-201"}` → get a thread ID.
3. `POST /api/chat` with `request_id`, `user_id`, `thread_id`, `text`.
4. Inspect returned `answer`, `components`, `citations`, `conflicts` and `limitations`. Components contain exact stored result rows; the model only describes presentation.
5. Use `/api/threads/{id}/messages?user_id=...`, `/api/results/{id}?user_id=...` or `/api/evidence/{id}?user_id=...` for saved detail. URL-encode a source section's `#` as `%23`.

Reuse a request ID only to retry the **same** text/user/thread. Completed requests return their saved answer; mismatched IDs and overlapping requests are rejected. A retry does not duplicate saved turns or a shared change.

This is a **local demo user picker**, not authenticated access control for public deployment. Selected-user ownership is enforced for private threads/results, but anyone with local API access can select a dataset user. Keep it bound to loopback.

## Checks and references

```sh
python3 -m pytest -q
```

Tests use temporary databases. Runtime databases and credentials are ignored; source data/research is preserved. Calculations use 16 October 2026, separate from conversation timestamps. New records can be loaded with the same loader; conflicting existing IDs fail without discarding active data or runtime feedback.

Read [system design](docs/system-design.md), [contracts](docs/contracts.md), [state](tasks/state.md) and [backend interfaces](tasks/briefs/backend-interfaces.md) for development. Worker ownership/reports remain in `tasks/`; the overall checklist still includes future frontend and submission work.
