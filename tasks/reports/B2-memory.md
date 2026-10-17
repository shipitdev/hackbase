# Worker report: B2 — private conversation/results backend

**Worker/model/effort:** GPT-6 worker session; exact model/effort not exposed here  
**Status:** accepted by Sol  
**Interface revision:** backend contract v1

## Delivered

Implemented `MemoryStore` with explicitly closed per-operation SQLite connections, user-owned threads/results, persistent messages and full saved SharedRows, bounded context with exact IDs and earlier references, request state/idempotency, and bounded traces stored outside chat context. Assistant recall includes explicit answer IDs and well IDs from only its referenced results; evidence refs are not treated as wells. Context derives discussed IDs from saved messages, so undisplayed query results do not appear as discussion history. First requests also title new threads from the user's text. A thread allows one in-progress request at a time. Tests cover restart recall, cross-user denial, busy/mismatched/cached requests, failed retries, result persistence, trace isolation and unrelated-result isolation.

## Checks

| Command or manual check | Outcome | Evidence / exact failure |
|---|---|---|
| `python3 -m pytest tests/test_memory.py -q` | pass | 7 passed in 0.15s |
| `git diff --check` | not run | Workspace root is not a Git repository; Git reported “Not a git repository.” |

## Limits and decisions needed

Context includes up to 12 current-thread messages/12,000 text characters, up to 12 older reference previews, and up to 200 exact IDs. Traces retain at most 1,000 rows and truncate each serialized argument/outcome to 4,000 characters. No frontend/provider/network integration was exercised.

## Handoff

Files no longer being edited: `app/memory.py`, `tests/test_memory.py`, this report. Sol can rerun the focused pytest command above. **Sol review:** accepted after review, repairs and combined backend checks. Live-provider/frontend acceptance is pending.
