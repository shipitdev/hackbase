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
