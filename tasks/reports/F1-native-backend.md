# Worker report: F1 — native OpenUI backend

**Worker/model/effort:** Assigned GPT-6 Luna high (orchestrator dispatch); worker runtime label GPT-6
**Status:** complete-for-review
**Interface revision:** Native OpenUI v2, 17 October 2026

## Delivered

Live model instructions now require native OpenUI Lang (`ui` string or null) and include the generated library prompt. The backend calls the official Node `validateProgram` bridge over bounded stdin/stdout with a timeout, then checks ownership, same-thread scope, current knowledge revision, columns, completeness and citations before returning `ui_format`, `ui_version`, `ui`, and only referenced saved results. Historical v1 answer parsing was not added; the strict draft rejects component manifests. Parser failures get the existing single repair attempt and end in the existing safe partial response when unresolved.

The bridge API is `app.openui.validate_ui(program, results)` and returns `{type, result_id, title, mapping}` descriptors for internal server validation. Added `tests/test_openui.py` and migrated relevant `tests/test_agent.py` fixtures. UI data was sourced from the scripted saved-result test fixtures; no live provider call was made.

## Checks

| Command or manual check | Outcome | Evidence / exact failure |
|---|---|---|
| `pytest -q tests/test_agent.py tests/test_openui.py` | pass | 20 passed in 19.15s |
| `node --import tsx scripts/check-openui.tsx` (from `frontend/`) | pass | OpenUI P0 generated prompt/schema, parser restrictions and result-backed rendering passed |

## Limits and decisions needed

The native prototype supports the contract's proven Card/Table library; other four display types remain a later frontend slice. No paid/live model call or full app acceptance was run.

## Handoff

Changed files: `app/agent.py`, `app/contracts.py`, `app/openui.py`, `frontend/scripts/validate-openui.tsx`, `tests/test_agent.py`, `tests/test_openui.py`. These files are ready for Sol review. Root can reuse `validate_ui` for the live checker.

**Sol review:** accepted after code review and integrated78-test/live-browser checks; see F3-prototype-acceptance.md.
