# Orchestrator state

Updated 17 October 2026. **Current phase: Q1 data/source acceptance and native OpenUI P0 complete; native backend contract + browser UI next.**

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
- User granted full permissions/network access. Root initialized local Git, fetched origin/main and aligned its index without changing working files; normal checkout now tracks https://github.com/shipitdev/hackbase. .env/runtime databases/node_modules remain ignored. DNS and DigitalOcean catalog access now work; earlier sandbox blockers are historical.

## Current assignments / ownership

| Owner | Files | Status |
|---|---|---|
| B6 Luna high | scripts/check_backend_question.py; tests/test_backend_question.py; reportB6 | Released; root accepts real Q1 data/source checks as pass_with_limitations. |
| F0 Luna medium | frontend/package files, frontend/src/genui/**, frontend/scripts/**; reportF0 | Released and reviewed. Official parser, trusted Card/Table bindings, same-library artifacts and SSR proof pass. |
| Sol | Root docs/state/setup, backend contracts/integration, review and GitHub sync | Native OpenUI plan saved; v2 backend migration not yet implemented. |

## Live backend check

B6 created an opt-in command: `python3 scripts/check_backend_question.py`. It uses a SQLite backup of shared data and temporary private memory, sends one actual status question, and checks its answer/card against independent latest-inspection data and resolved inspection/manual/context evidence. No shared corrections/history are changed by this check.

After full permissions, root catalog GET succeeded. Live Q1 returned correct source-backed data with caveats. Root fixed general citation collection for source IDs explicitly mentioned in answer/limitations/conflicts, then independently revalidated the final actual response: **pass_with_limitations**, not an uncaveated complete answer. Exact latest state:INS-0001-0203,25.6C wellhead,22.4C ambient,3.2C delta,15C threshold, producing0. All seven final source citations resolve and saved component data matches a complete query result.

The harness had also imposed exact caveat wording ('after', selected work-order phrases). Those were removed while retaining numeric/time/source/result checks and requiring explained limitations. A regression rejects incorrect production values. Full backend suite70passed before the last checker-only change; final checker5tests pass. Original private answer and validation summary remain ignored under data/checks/. Five kimi-k3 calls took82317ms; optimize latency before demo rather than claiming it is fast.

## OpenUI plan / next actions

1. P0 is reviewed and passes official parsing, restrictions, schema/prompt drift and SSR for trusted Card/Table values. Root pinned transitive katex0.18.2 to fix the five reported low findings; npm install/audit reports0 vulnerabilities and both OpenUI/KaTeX rendering checks pass.
2. P0 passes; next freeze native UI contractv2, using official parser validation and the existing result ownership/column/revision checks. Retain old answers without rewriting history. No custom language parser or duplicate model-authored JSON UI manifest.
3. Build user/thread chat shell + sources, then all six displays and actual browser checks. Existing Excalidraw layout remains the reference.
4. After native response migration, rerun live Q1 and then the18 scenarios with actual model answers, corrections and user switching. Preserve analysis/conversation dates separately.

## Read on resume

AGENTS.md → docs/05-frontend-openui.md → docs/contracts.md → relevant worker report and tasks/todo.md. Original dataset/ and opencode/ remain untouched. Submission, released test data and final artifact work remain pending.
