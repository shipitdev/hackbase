# Orchestrator state

Updated 17 October 2026. **Current phase: working native OpenUI Card/Table chat prototype accepted; remaining four displays and improvements next.**

## Decisions and boundaries

- Sol orchestrates; Luna high for backend/domain/debugging, medium for bounded UI. Fresh bounded assignments, exact file ownership, no child agents or routine polling. Workers notify completion/blockers. Saved files carry context.
- Analysis date **2026-10-17**. Historical16October fixtures stay historical; conversation dates are separate.
- Runtime DigitalOcean `inference-router`, preference `budget`; user restored original working account/key and **$25** budget. No hard dollar cap is enforced. Ignored .env mode0600; never publish credentials or runtime conversations.
- User chose **direct model-generated OpenUI Lang**. Native v2 contract is implemented; no parallel model-authored JSON visual manifest. Historical v1 answers retain their old data/format.
- User requested `npx skills add Leonxlnx/taste-skill`: installed locally with source lock. Default v2 excludes apps; original v1 app guidance used with saved sidebar/chat/evidence layout and no unnecessary motion/styling framework.
- Full filesystem/network permissions now work. Git repo tracks https://github.com/shipitdev/hackbase; runtime data, dataset/,opencode/,skills,node_modules and screenshots are ignored. No source dataset/research edits.

## Accepted implementation

FastAPI/SQLite restricted corrected queries, rule/report evidence, scoped shared corrections, private chats/results, idempotent retries, source citations and result provenance. Actual sample:200 wells, 39,567 inspections, 5,665 maintenance records, 1,509 readable reports. Repeat loading preserves feedback/history; collisions rejected safely.

Native backend adds `ui_format`, `ui_version`, `ui`, and referenced server-owned `results`. Official Node parser through bounded stdin/stdout; literal Card/Table-only program, no Query/Mutation/actions/dynamic expressions, same-user/thread/current-revision checks. Existing result/citation/completeness/privacy checks remain. Shared memory includes native displayed results; unused queries excluded.

React/Vite chat: real user/thread selection, new chat, persisted history, composer, native card/table, source panel, conflicts/limitations, loading/error/safe retry. Epoch guards ignore stale chat/source replies; switching user clears private state. Historical data remains readable. Responsive mobile navigation is inert when hidden with focus/Escape handling. OpenUI inspector auto-mount disabled via documented pinned-version shortcut in src/openui-bootstrap.ts because its toggle covered Send.

## Current ownership

F1 Luna high and F2 Luna medium completed, reviewed, repaired and returned all files. No workers own active files. Sol owns integration/docs/Git acceptance. Reports:tasks/reports/F1-native-backend.md,F2-chat-shell.md,F3-prototype-acceptance.md. Earlier backend reports remain historical evidence.

## Verification

- Full backend suite **78 passed**, 48 upstream deprecation warnings, 52.83s. No paid calls in tests.
- OpenUI official parser/schema/prompt/SSR check passes; strict TypeScript + Vite production build passes; npm audit: 0 vulnerabilities.
- Real browser question: first request provider timeout; one manual same-ID retry succeeded in **64065ms**, native status card+context table,7 sources. Independent latest-data/source/result checks **pass_with_limitations**. Two persisted messages, no duplicate user turn. Private snapshot ignored at data/checks/native-browser-answer.json. No further live calls needed for this slice.
- Actual evidence API, user switching and history restoration pass. Mocked browser retry/edited-retry/late-private-response/evidence-close and mobile keyboard states pass. Widths320/390/768/1440 have no page overflow; desktop/mobile screenshots inspected. Final navigation console no warnings/errors.

## Run

Backend: `python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.
Frontend: `npm --prefix frontend run dev` → http://127.0.0.1:5173.
Both local servers were started for acceptance. README covers fresh setup. Node22.12+ and frontend dependencies are also required for native backend validation. Do not expose this demo user picker publicly as authentication.

## Next

1. User tries prototype; then improve answer brevity, status labels/units and model latency/timeouts.
2. P3: remaining bar/line/map/heatmap bindings with trusted saved data, stopped markers, zero cells, coordinate fallback. Preserve native parser boundary and component combinations; no duplicate JSON manifest.
3. All 18 live scenarios including shared feedback/private recall/user switching and released test dataset. Existing tests/liveQ1 are not evidence all 18 pass.
4. Submission/license/video/released-data work remains pending. Keep docs/05-frontend-openui.md,contracts.md and tasks/todo.md current.

## Active E1 evaluation
User authorized Luna to run all18 backend live questions without Playwright and instructed Sol not to run them. E1 Luna high exclusively owns scripts/evaluate_questions.py,tests/test_evaluate_questions.py,tasks/reports/E1-live-18.md and ignored data/evaluations/e1/**. Production code/config/demo databases unchanged. Isolated sequential scenarios, one paid attempt per required turn, resumable per-step evidence; data/memory and unsupported-visual results separate. Sol waits for completion/blocker and reviews report only, no rerun. Brief:tasks/briefs/E1-live-18.md.

## E1 result and active repairs
E1 returned:29 required turns,19 HTTP200 partial answers,8 errors,2 dependency-blocked. No full18pass claim. Report reviewed; root read traces only, did not execute evaluation. Confirmed SQLite dialect errors (ILIKE/typed date literals), tool-batch guard failures, timeout opacity, Q18 disagreement status and unsupported four visuals. Token usage lower bound1,291,630; error calls missing usage, cost unknown. No second paid benchmark authorized in this slice.
R1 Luna high owns app/agent.py,provider.py,tests/test_agent.py,test_provider.py and reportR1 for bounded reliability fixes/offline regressions. E2 Luna medium owns scripts/evaluate_questions.py,tests/test_evaluate_questions.py,reportE2 and ignored review/** for offline harness audit/repair; original E1 outcomes immutable. Sol owns conflict policy after R1 returns agent.py, shared contracts/state/integration. Workers notify once complete/blocker, no polling.

R1 review: cap oversized-batch repair to one attempt; ownership explicitly expanded to app/main.py and tests/test_api.py for allowlisted error evaluation_metadata. Root has not edited active worker files. Q18 conflict policy change deferred: official answer yes with both notes was delivered; E2 is clarifying semantics rather than claiming categorical factual failure.

## Accepted post-evaluation repairs

R1 and E2 returned all files. Sol reviewed source and test evidence; no active worker ownership. R1 worker-run51 focused runtime/API/provider tests pass; E2 worker-run11 offline harness tests pass plus compilation. Sol did not execute or rerun the18-question evaluation. No new paid calls or runtime model/budget changes.

Implemented SQLite-specific date/filter/parameter guidance, concise answers, one shared bounded repair for excessive tool batches (zero tools execute in rejected batches), safe partial reasons/latency, and allowlisted aggregate metadata on original HTTP errors. SQL restrictions,8tools/8rounds/120s/96kcharacter limits remain intact. External provider timeouts unresolved.

Evaluator now fences dispatch before paid calls, refuses ambiguous automatic replay, verifies prerequisite persisted state/exact Q6 list, uses user-qualified thread keys, records snapshot provenance and distinct ordered per-message timestamps with clock restoration, and captures new safe error usage metadata. Root caught/fixed module shadowing and same-turn timestamp issues through worker follow-up. Original E1 artifacts unchanged; reviewed sanitized18-row table is tasks/reports/E1-reviewed-results.md. Q18 official yes answer plus both notes aligns; resolved wording is a semantics concern, not proven wrong spill conclusion. No blanket conflict-status rewrite.

Next: add four native result-backed displays; then delegate a small targeted live recheck of repaired failures with fresh isolated states, before another full18run. The current runner preserves E1 and will not automatically replay it; fresh evaluation output handling and missing Q16 prior-Michael-history setup still need attention for a full repeat. Failures after accepted writes must be interpreted from persisted state, not assumed rollback. Do not claim all18passed or that provider timeouts are solved.
