# Backend integration — Sol

Backend implementation is saved in `app/`. Frontend work is pending. Sol accepted both worker slices after review and requested repairs.

Implemented: FastAPI routes, configurable Chat Completions adapter, five-tool loop, saved query-backed component descriptions, resolved source/private-message citations, scoped shared changes, private conversation/results, request retries, and repeatable data loading. Data and memory were delegated to Luna high with separate file ownership; workers reported completion. Sol reviewed and integrated their code. An independent worker review found missing citation enforcement and total prompt limits; both were fixed with regression tests.

Verification so far:

- `python3 -m pytest -q`: 35 passed after the final data repair, including the real sample through the HTTP/tool/result/source path with a scripted model. Installed FastAPI emits deprecation warnings on Python 3.14; these do not fail the tests.
- `python3 -m app.load dataset/sample-data --db data/knowledge.sqlite`: 200 wells, 39,567 inspections, 5,665 maintenance records, 1,509 readable reports, five rule documents; no collisions or broken links.
- Real loaded database via FastAPI TestClient: health/users/OpenAPI return 200; data ready=true, chat_ready=false because no runtime model key is configured.
- Uvicorn reached application startup, then this workspace rejected binding to 127.0.0.1:8000 with Operation not permitted. No external-port smoke is claimed.

Final data regressions pass (seven store tests), including single-quoted SQL identifiers, expired measurements, and retained claim text. A subsequent citation-scaling fix keeps full contributor lists in saved results and resolves selected sources separately; all 12 agent tests pass. The real-data integration was rerun after that fix.

Remaining acceptance: live provider and frontend. No live provider request, frontend/browser rendering, complete 18-question model evaluation, released test dataset or submission work has been checked. The demo user picker enforces selected-user ownership but is not authentication; run locally. Report parsing uses known explicit patterns and preserves full text for unknown wording. No application Git repository/commit exists: .git creation was blocked by workspace permissions.

Provider direction: user prefers Gemma 4 or a free provider. The backend defaults to OpenRouter's tool-capable Gemma free endpoint; another Chat Completions endpoint or local Ollama can be configured. OpenCode editor access does not itself supply a backend API key. Credentials remain outside project files. See README.md and .env.example.
