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

DigitalOcean serverless inference is the current setup. Copy `.env.example` to `.env` if it is absent, then paste your **model access key** into `GRADIENT_MODEL_ACCESS_KEY`. Do not paste it into chat or commit it. The backend automatically reads this project's `.env`; existing shell settings take precedence. Restart the server after changing the file.

The endpoint is `https://inference.do-ai.run/v1`. The provider uses OpenAI-compatible **Chat Completions** with function tools. See [DigitalOcean setup and budget](docs/digitalocean.md) for the selected model, pricing sources and inexpensive connectivity test. A generic `LLM_API_KEY` is also supported.

Other providers remain configurable through `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY`. OpenRouter also accepts `OPENROUTER_API_KEY`. For local Ollama, use `http://127.0.0.1:11434/v1` and an installed tool-capable model; loopback providers need no key. OpenCode editor access alone does not configure backend model access.

Missing credentials produce an explicit error. Automated tests use scripted models/HTTP transports; they do not establish live model answer quality. No automatic provider fallback or retry loop spends extra credits.

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

Tests use temporary databases. Runtime databases and credentials are ignored; source data/research is preserved. Calculations use 17 October 2026, separate from conversation timestamps. New records can be loaded with the same loader; conflicting existing IDs fail without discarding active data or runtime feedback.

Read [system design](docs/system-design.md), [contracts](docs/contracts.md), [state](tasks/state.md) and [backend interfaces](tasks/briefs/backend-interfaces.md) for development. Worker ownership/reports remain in `tasks/`; the overall checklist still includes future frontend and submission work.

## OpenUI compatibility proof

```sh
npm --prefix frontend ci
npm --prefix frontend run check:openui
```

This checks native OpenUI parsing, result-backed Card/Table widgets, schema/prompt drift, rejected dynamic programs, and ReactDOM server rendering. It is not a complete browser app yet. See the [native OpenUI plan](docs/05-frontend-openui.md). Dependencies are pinned; a targeted KaTeX override fixes the reported low-severity audit chain.

The opt-in real backend check is `python3 scripts/check_backend_question.py`. It can report `pass_with_limitations` when the answer's data and sources pass but observation/provenance caveats remain. It uses the configured paid provider and isolated temporary state.
