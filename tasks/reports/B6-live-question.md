# B6 — live backend Q1 question check

**Worker/model/effort:** GPT-6 Luna / high (explicit assignment)  
**Status:** partial  
**Interface revision:** backend contracts v1

## Delivered

Added `scripts/check_backend_question.py` for one opt-in `/api/chat` question. It snapshots `data/knowledge.sqlite` using SQLite backup, independently reads the latest WELL-0001 inspection, uses temporary private memory, and checks the completed status card against its retained result and the inspection, manual, and Q1 planned-shut-in citations. The output contains only safe metadata. `tests/test_backend_question.py` exercises this path with a scripted provider and temporary data; no paid calls run in tests.

## Checks

| Command or manual check | Outcome | Evidence / exact failure |
|---|---|---|
| `python3 -m pytest -q tests/test_backend_question.py` | pass | 1 passed; 16 installed FastAPI/Python 3.14 deprecation warnings |
| `python3 scripts/check_backend_question.py` | fail | One authorized live request returned API HTTP 502 with `provider_error`; no completed answer or acceptance evidence. The CLI version used for this single request printed only `Live question check failed: provider_error: The backend question request failed`. No provider response body or credentials were saved. |

## Limits and decisions needed

Live model/tool behavior remains unverified. The failure did not expose whether the cause was endpoint reachability, provider response, or account access, so it cannot be attributed specifically to DNS. The harness now includes the API's safe structured error message in future output, but the paid request was not repeated. No frontend work was performed.

## Handoff

Changed files are `scripts/check_backend_question.py`, `tests/test_backend_question.py`, and this report. Sol can reproduce the no-cost harness test with the pytest command above. The next live command, when appropriate, is `python3 scripts/check_backend_question.py`; it requires a reachable configured provider. No broad question run or frontend implementation is included.

**Sol review:** harness reviewed; Sol corrected overly strict exact-one-card acceptance so legitimate card-plus-table answers are allowed and each displayed result is checked against its own saved rows. Two mocked tests pass. Live Q1 remains unverified; user was given the normal-terminal command.
