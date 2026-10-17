# Worker report: F2 — chat shell

**Worker/model/effort:** GPT-6 Luna, medium  
**Status:** complete-for-review  
**Interface revision:** Native OpenUI v2 frozen contract, 17 October 2026

## Delivered

Implemented the native chat shell in `frontend/src/App.tsx`, `api.ts`, `types.ts`, `components/AnswerView.tsx` and `styles.css`. It loads users and owned threads from the API, creates/selects threads, restores saved messages, submits/retries with a stable request ID, ignores stale responses after switching user/thread/source, renders validated OpenUI via the installed Renderer/ResultsProvider, and shows historical v1 result rows with a historical label. Same-thread selection is a no-op, retries reuse an ID only when the composer text is unchanged, and synchronous guards prevent duplicate sends/thread creation. Hidden mobile navigation and evidence panels use `inert`/`aria-hidden`; opening, closing and Escape return/manage focus. Text/control sizes and contrast are raised and the composer uses a flat background. The prototype uses no mocked users, threads, or answer data.

## Checks

| Command or manual check | Outcome | Evidence / exact failure |
|---|---|---|
| `npm --prefix frontend run build` | Pass | TypeScript and Vite production build passed. Vite emitted dependency module-directive warnings. |

## Limits and decisions needed

No browser/API manual walkthrough was run. Historical non-table visual types display their saved source rows as readable tables rather than recreating the old chart/map renderer.

## Handoff

F2 files are no longer being edited. Sol can rerun `npm --prefix frontend run build`.  
**Sol review:** accepted after repairs, real browser/source/history checks and responsive inspection; see F3-prototype-acceptance.md.
