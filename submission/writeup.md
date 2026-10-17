# Asset Intelligence Copilot — submission draft

## Problem and approach

Operators ask questions across inspection records, maintenance reports, operating rules and earlier discussions. The copilot uses read-only SQLite queries for calculations and cites the records behind an answer. Production is calculated from temperature above ambient, with type-specific thresholds; downtime follows the challenge's inspection convention. Calculation date:17October2026.

A React chat interface renders native OpenUI programs chosen by the runtime model. Numbers come from saved query results, never model-authored arrays. A Node process runs the official parser and rejects executable actions or dynamic programs. The server checks user/thread ownership, source revision and column types before publishing a visual.

## Memory and corrections

Shared well facts and scoped corrections are stored separately from private user chats. Original readings remain available. Accepted field/rule changes affect later calculations at their stated scope. User switching does not expose another user's history. This is a local demo user picker, not public authentication.

## Implementation and models

FastAPI, SQLite, React/Vite, OpenUI and Leaflet. DigitalOcean inference-router with budget preference is the runtime model route. Actual serving model IDs and reported token usage are retained where available. Build work used Sol orchestration and bounded Luna assignments; these are separate from the runtime model. Credentials and runtime conversations are excluded from the repository.

## Observed results and limitations

See tasks/reports/E1-reviewed-results.md for the sample18-question evaluation. It contains partial answers, failures and unverified dependent scenarios; it is not an18/18 pass. Runtime repairs and visual completion have separate reports. No dollar cost is claimed from incomplete usage. Provider latency/timeouts remain a limitation. Released dataset results must be recorded separately once available.

## Final packaging still required

- Fill released-data results from observed answers, with source support and failures.
- Add the repository's license after confirming the intended license.
- Export a readable2–3page write-up and record a narrated demo of at most5minutes.
- Verify repository, video and write-up links; submit only with user authorization.
