# Worker report: F7 — Send button visibility

**Worker/model/effort:** UI worker; model/effort not exposed
**Status:** complete-for-review
**Interface revision:** Native OpenUI v2, frozen 17 October 2026

## Delivered

Constrained the app shell to one shrinkable viewport row and allowed the thread list and conversation to scroll within it. Added a bounded, internally scrollable provider error message so long errors leave the composer and Retry control visible. Replaced the icon-only submit control with a clear Send/Sending… label and stable button width. Changes are limited to `frontend/src/App.tsx` and `frontend/src/styles.css`; no data was mocked.

## Checks

| Command or manual check | Outcome | Evidence / exact failure |
|---|---|---|
| `npm run build` (from `frontend/`) | pass | TypeScript and Vite build succeeded. Existing dependency `use client` bundling warnings; full output at `/tmp/f7-frontend-build.log`. |
| Browser checks at requested viewports/states | not run by this worker | Orchestrator handling browser reproduction and responsive checks. |

## Limits and decisions needed

No known code limitation. Browser checks should include the 600-character error case at 400px height.

## Handoff

Files no longer being edited: `frontend/src/App.tsx`, `frontend/src/styles.css`, `tasks/reports/F7-send-button.md`. Orchestrator can verify with `npm run build` from `frontend/` and its browser scenarios.

**Sol review:** accepted. Root restored the existing accessible Send-question label and removed the hard320px body minimum that clipped Send in zoomed narrow views. Browser20checks across empty/typed/busy/600+character-error/long-generated-table states at effective CSS widths256/312/614/1152 passed: button on-screen/uncovered, body fits viewport, clear Send/Sending label. Final production build passes. No paid calls. Historical saved chats unchanged.
