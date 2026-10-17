# Worker report: R1 — runtime reliability

**Worker/model/effort:** GPT-6 Luna high
**Status:** complete-for-review
**Interface revision:** OpenUI v2 / current contracts

## Delivered

E1 traces confirm Q6’s PostgreSQL-style date literals and Q7’s `ILIKE` failed twice; Q18’s multi-statement query was correctly blocked. Q9’s >8-call batch previously failed before execution. `app/agent.py` now teaches SQLite date/filter/parameter syntax and concise cited prose, and allows one bounded batch repair; a second oversized batch returns a reasoned partial without executing its calls. Partial answers include specific failure reasons and elapsed time. Provider failures remain errors with aggregate metadata. `app/main.py` serializes only `served_models`, numeric `usage`, and `latency_ms`, preserving HTTP status/code/message.

## Checks

| Command or manual check | Outcome | Evidence / exact failure |
|---|---|---|
| `python3 -m pytest -q tests/test_agent.py tests/test_api.py tests/test_provider.py` | Pass | 51 passed in 13.83s; 40 upstream FastAPI deprecation warnings. Covers one-repair limit/no writes, safe timeout metadata, and same-ID retry without duplicate user message. |

## Limits and decisions needed

External provider timeouts remain unresolved and are not retried. No live provider call was made. Conflict behavior remains out of scope.

## Handoff

Ownership returned for `app/agent.py`, `app/main.py`, `tests/test_agent.py`, `tests/test_api.py`, and this report. **Sol review:** accepted after source review, bounded-repair follow-up and worker-run51-test evidence. No fresh live-model success is claimed.
