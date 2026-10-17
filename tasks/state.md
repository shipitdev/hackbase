# Orchestrator state

Updated 17 October 2026. **Current phase: real backend question acceptance + native OpenUI frontend plan/compatibility check.**

## User decisions

- Sol is the sole orchestrator; Luna high handles backend/domain work, medium handles bounded UI/proofs/docs. Exact file ownership; no recursive agents or worker polling. Workers report completion/blockers. Conserve tokens and do not repeat unchanged checks.
- Analysis date **2026-10-17**, explicitly corrected by user. Original16 October sample anchors remain historical tests.
- DigitalOcean managed `inference-router`, routing preference `budget`. User restored the original key/account, reports the small tool smoke worked, and restored the budget to **$25**. This is not an app-enforced dollar cap.
- Model access key lives only in ignored root .env (mode0600). Never echo or publish it. No dedicated GPU, droplet, model gateway or additional UI model authorized/needed.
- User selected **direct model-generated OpenUI Lang**, not JSON-to-OpenUI translation. Follow docs/05-frontend-openui.md. Full UI must support card/table/line/bar/map/heatmap, combinations, sources, private memory and corrections.

## Implemented and verified

- FastAPI + SQLite backend, restricted corrected SQL views, source/report search, shared corrections and rule scope, private chats/results, deduplicated requests, citations and saved component data.
- B1/B2 accepted after review and repairs. B3/B4/B5 provider/diagnostic/router work reviewed; serving model IDs are retained per call. Reports under tasks/reports/.
- Actual sample loaded:200 wells,39,567 inspections,5,665 maintenance records,1,509 readable reports. No collisions/broken links in the recorded load.
- Backend automated checks include real sample HTTP/tool/result/private-recall path with scripted models. These do not establish live model accuracy or browser rendering.
- Local .git creation and socket binding are blocked. GitHub sync uses connector commits to https://github.com/shipitdev/hackbase. Router support, the Q1 harness and the native OpenUI plan are synced as separate reviewable commits through that connector. Credentials, runtime DBs, dataset and research checkouts are excluded.

## Current assignments / ownership

| Owner | Files | Status |
|---|---|---|
| B6 Luna high | scripts/check_backend_question.py; tests/test_backend_question.py; reportB6 | Released; root reviewed and fixed overly strict single-card acceptance. Two mocked harness tests pass. |
| F0 Luna medium | frontend/package files, frontend/src/genui/**, frontend/scripts/**; reportF0 | Released blocked: npm registry DNS failure. Only provisional package.json exists; no parser/render proof. |
| Sol | Root docs/state/setup, backend contracts/integration, review and GitHub sync | Native OpenUI plan saved; v2 backend migration not yet implemented. |

## Live backend check

B6 created an opt-in command: `python3 scripts/check_backend_question.py`. It uses a SQLite backup of shared data and temporary private memory, sends one actual status question, and checks its answer/card against independent latest-inspection data and resolved inspection/manual/context evidence. No shared corrections/history are changed by this check.

The worker's one live attempt returned API502 provider_error; the actual reason was not recorded in that first attempt. It is not a live pass and cannot be specifically attributed to DNS. The script now prints safe structured error details for the next attempt. No retries/benchmark were run. Normal-terminal live acceptance remains required because agent workspace networking has been blocked previously.

## OpenUI plan / next actions

1. User was asked to run `python3 scripts/check_backend_question.py` and `npm --prefix frontend install --save-exact` in the normal terminal. Await backend JSON/error and install completion. Then finish F0 headless parser, same-library schema/prompt, result binding and renderer proof. Sol confirmed ENOTFOUND registry.npmjs.org with one bounded no-retry npm metadata check. Do not claim a render/build from the manifest alone.
2. On success, freeze native UI contractv2, using official parser validation and the existing result ownership/column/revision checks. Retain old answers without rewriting history. No custom language parser or duplicate model-authored JSON UI manifest.
3. Build user/thread chat shell + sources, then all six displays and actual browser checks. Existing Excalidraw layout remains the reference.
4. Run live Q1, then the18 scenarios with actual model answers, corrections and user switching. Preserve analysis/conversation dates separately.

## Read on resume

AGENTS.md → docs/05-frontend-openui.md → docs/contracts.md → relevant worker report and tasks/todo.md. Original dataset/ and opencode/ remain untouched. Submission, released test data and final artifact work remain pending.
