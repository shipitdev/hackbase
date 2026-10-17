# Orchestrator state

Updated 17 October 2026. **Final dataset activated; Luna high running the 11 final scenarios / 21 turns.**

## Stable decisions

- Sol sole orchestrator; Luna high for backend/data/debugging, medium for bounded UI. Exact file ownership, fresh scoped context, no child agents/status polling. Workers notify completion. Active final evaluation ownership is listed below.
- Analysis date **2027-01-15**; conversation time separate. Historical16October fixtures retained.
- Runtime DigitalOcean `inference-router`, budget preference, user budget$25 (no hard cap). Key only ignored.env, never print/publish. No runtime model change or paid test in final sprint.
- Direct model-generated OpenUI Lang; same-library schema/prompt. No model-authored rows or arbitrary browser code/actions. Root/server owns calculations/results/private identity. Demo user picker is not public authentication.
- GitHub shipitdev/hackbase; dataset/,opencode/ preserved/ignored. Runtime databases/chats/screenshots/keys and installed .agents/skills ignored. Taste skill installed; original v1 app guidance used because default v2 excludes apps.

## Implemented

FastAPI/SQLite corrected restricted queries, reports/rules/evidence, scoped shared corrections preserving originals, private chats/results, idempotent retries. Final release600wells/125198inspections/17415maintenance/4437readable reports loaded; original sample backed up. Loader rejects collisions and preserves history/feedback.

Native six-view contract in docs/contracts.md: Card/Table/Bar/Line/Map/Heatmap, max6 static views. Official Node parser, same-user/thread/revision and full-row numeric/coordinate/boolean/cell checks; only server-saved values hydrate. Current prompt teaches SQLite and explicit heatmap zero-grid queries. One shared bounded repair for oversized tool batches/final validation,8rounds/120s/96k context retained. Original provider HTTP errors expose only safe accumulated model/usage/latency metadata.

React chat: real users/threads/history, source panel, conflict/limitation states, safe explicit retry, stale reply guards and private-state clearing. Six displays stack at readable answer width. Full viewport grid/flex min-size fixes and scoped scrolling prevent generated outputs moving/expanding outer page. Wide tables/line plots scroll internally. Leaflet map observes resize and has tile-failure/coordinate-table fallback. OpenUI inspector disabled via documented pinned-version bootstrap shortcut.

## Evidence and limits

- E1 all18 sample scenarios attempted:29turns,19HTTP200 partials,8errors,2blocked. **Not18/18passed.** Reviewed table tasks/reports/E1-reviewed-results.md. Several shared writes persisted despite response timeouts; never assume rollback. Q18 yes+both notes aligns with official source; resolved wording needs semantics review, no blanket conflict rewrite.
- R1 worker51 focused runtime/API/provider checks; E2 worker11 offline runner checks. Runner fences paid dispatch/replay, checks persisted prerequisites/exact Q6 list, owner-qualifies threads, orders per-message timestamps/restores clock and captures safe error metadata. Original E1 immutable. Fresh output selection/Q16 prior-history setup remain limitations before another full run.
- Final sprint root44 focused backend/parser/API/preflight tests passed; final OpenUI six-view SSR/parser/bridge/example checks and strict TS/Vite build pass. npm audit0.
- Actual browser six-view fixture with35rows/20columns/longtext at320/390/768/1024/1440 and resize-back: viewport stable, composer visible, internal scrolling,0visual errors. Map3points/popup/realtiles and blocked-tile fallback checked. Screenshots inspected and ignored. These prove rendering, **not live model selection or final question correctness**.
- Prior actual Q1 native Card+Table passed data/source checks with limitations after manual retry,64s. Provider timeouts/latency still unresolved. No broad paid rerun.

## Release readiness and immediate next actions

1. Final baseline activated from official commit009e2b5; see docs/released-data.md. Version dataset-7207fefc8284, revision1, analysis2027-01-15. Both databases backed up; private memory counts verified unchanged.
2. Delegate targeted live checks/new final questions with isolated/resumable evidence capture. Preserve scenario dependencies and private history. Do not let old E1 --resume silently represent a new run.
3. Complete submission/writeup.md from actual results, select/add license, export2–3pages, record<=5minute demo, verify links. No event submission without authorization.

## Run / references

Backend localhost8000: `python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.
Frontend localhost5173: `npm --prefix frontend run dev`. Node22.12+ and frontend dependencies also needed by backend validator. Both local servers are running; backend was restarted with final Python integration.

Current plan tasks/plan.md final-priorities section; checklist tasks/todo.md. Reports F6-final-sprint.md, F4-layout.md, F5-six-visuals.md, D1-release-readiness.md, R1-runtime-reliability.md, E2-evaluation-review.md. Generated schema/prompt `npm --prefix frontend run check:openui -- --write`; normal check catches drift. Submission draft is not final/complete.

## Accepted F7 Send-control fix
Luna medium implemented shrinkable grid row/sidebar and bounded scrollable error text; Send/Sending label retained with existing accessible name. Root removed hard320px body min-width that clipped zoomed narrow views.20browserchecks across empty/typed/busy/long-error/generated-table at CSS widths256/312/614/1152 pass; final frontend production build passes. No paid model calls; no backend restart needed. All F7 files returned. Report tasks/reports/F7-send-button.md.

## Final release activation in progress
- Official dataset commit `009e2b5`; final release 600 wells/7 areas, today 2027-01-15, 11 ordered multi-turn questions.
- Backup: ignored `data/backups/before-final-20261017-164055/`; both SQLite stores preserved; zero shared changes at backup. Backend restarted PID32961, exec session36170, health ready/chat_ready.
- D2 compatibility accepted; ownership returned. T500 thresholds, source data corrections, history/status/raw payload columns integrated. Worker8 focused tests pass; root release test1pass, agent20pass, API4pass; frontend build pass.
- Ownership active: final_eval Luna high owns scripts/evaluate_final.py, tasks/reports/E3-final-evaluation.md and private data/evaluations/final-release/. Root authorized paid run after activation. Snapshot isolated, ordered, no automatic retries; root does not run paid evaluation.

## Video assignment
- Accepted video_demo Luna medium; ownership returned: docs/diagrams/video-system.excalidraw, docs/diagrams/video-system.svg, submission/pitch-script.md, tasks/reports/V1-video-demo.md. One-/two-word diagram labels, database shapes, actual runtime flow, simple narrated script; accuracy placeholders pending E3. No application changes or paid calls.

V1 accepted: 16:9 editable Excalidraw + SVG, mixed shapes/database cylinders, five tools and saved-result/nativeUI flow reviewed. Pitch script ~90sec design + live demo + results placeholders, total<5min. MCP checkpoint397bfffa662d43ee82. User records narration/demo; final accuracy still awaits E3.
