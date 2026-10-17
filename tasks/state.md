# Orchestrator state

Updated 17 October 2026. **Final sprint implemented: six native visuals + generated-output resize fix + released-data preflight. Await released dataset/questions.**

## Stable decisions

- Sol sole orchestrator; Luna high for backend/data/debugging, medium for bounded UI. Exact file ownership, fresh scoped context, no child agents/status polling. Workers notify completion. All latest assignments returned; no active file owners.
- Analysis date **2026-10-17**; conversation time separate. Historical16October fixtures retained.
- Runtime DigitalOcean `inference-router`, budget preference, user budget$25 (no hard cap). Key only ignored.env, never print/publish. No runtime model change or paid test in final sprint.
- Direct model-generated OpenUI Lang; same-library schema/prompt. No model-authored rows or arbitrary browser code/actions. Root/server owns calculations/results/private identity. Demo user picker is not public authentication.
- GitHub shipitdev/hackbase; dataset/,opencode/ preserved/ignored. Runtime databases/chats/screenshots/keys and installed .agents/skills ignored. Taste skill installed; original v1 app guidance used because default v2 excludes apps.

## Implemented

FastAPI/SQLite corrected restricted queries, reports/rules/evidence, scoped shared corrections preserving originals, private chats/results, idempotent retries. Original sample200wells/39567inspections/5665maintenance/1509readable reports loaded. Loader rejects collisions and preserves history/feedback.

Native six-view contract in docs/contracts.md: Card/Table/Bar/Line/Map/Heatmap, max6 static views. Official Node parser, same-user/thread/revision and full-row numeric/coordinate/boolean/cell checks; only server-saved values hydrate. Current prompt teaches SQLite and explicit heatmap zero-grid queries. One shared bounded repair for oversized tool batches/final validation,8rounds/120s/96k context retained. Original provider HTTP errors expose only safe accumulated model/usage/latency metadata.

React chat: real users/threads/history, source panel, conflict/limitation states, safe explicit retry, stale reply guards and private-state clearing. Six displays stack at readable answer width. Full viewport grid/flex min-size fixes and scoped scrolling prevent generated outputs moving/expanding outer page. Wide tables/line plots scroll internally. Leaflet map observes resize and has tile-failure/coordinate-table fallback. OpenUI inspector disabled via documented pinned-version bootstrap shortcut.

## Evidence and limits

- E1 all18 sample scenarios attempted:29turns,19HTTP200 partials,8errors,2blocked. **Not18/18passed.** Reviewed table tasks/reports/E1-reviewed-results.md. Several shared writes persisted despite response timeouts; never assume rollback. Q18 yes+both notes aligns with official source; resolved wording needs semantics review, no blanket conflict rewrite.
- R1 worker51 focused runtime/API/provider checks; E2 worker11 offline runner checks. Runner fences paid dispatch/replay, checks persisted prerequisites/exact Q6 list, owner-qualifies threads, orders per-message timestamps/restores clock and captures safe error metadata. Original E1 immutable. Fresh output selection/Q16 prior-history setup remain limitations before another full run.
- Final sprint root44 focused backend/parser/API/preflight tests passed; final OpenUI six-view SSR/parser/bridge/example checks and strict TS/Vite build pass. npm audit0.
- Actual browser six-view fixture with35rows/20columns/longtext at320/390/768/1024/1440 and resize-back: viewport stable, composer visible, internal scrolling,0visual errors. Map3points/popup/realtiles and blocked-tile fallback checked. Screenshots inspected and ignored. These prove rendering, **not live model selection or final question correctness**.
- Prior actual Q1 native Card+Table passed data/source checks with limitations after manual retry,64s. Provider timeouts/latency still unresolved. No broad paid rerun.

## Release readiness and immediate next actions

1. When source arrives, read docs/released-data.md. Run `python3 scripts/preflight_dataset.py <root> --db <new-stage.sqlite>`; also stage with `--base-db data/knowledge.sqlite`. Candidate-alone and merged counts/coverage/links/collisions reviewed before active load. Active knowledge+memory backed up consistently; no silent overwrite of conflictingIDs or feedback.
2. Delegate targeted live checks/new final questions with isolated/resumable evidence capture. Preserve scenario dependencies and private history. Do not let old E1 --resume silently represent a new run.
3. Complete submission/writeup.md from actual results, select/add license, export2–3pages, record<=5minute demo, verify links. No event submission without authorization.

## Run / references

Backend localhost8000: `python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.
Frontend localhost5173: `npm --prefix frontend run dev`. Node22.12+ and frontend dependencies also needed by backend validator. Both local servers are running; backend was restarted with final Python integration.

Current plan tasks/plan.md final-priorities section; checklist tasks/todo.md. Reports F6-final-sprint.md, F4-layout.md, F5-six-visuals.md, D1-release-readiness.md, R1-runtime-reliability.md, E2-evaluation-review.md. Generated schema/prompt `npm --prefix frontend run check:openui -- --write`; normal check catches drift. Submission draft is not final/complete.
