# B1 — Shared data backend

Model: GPT-6 Luna high. Goal: real sample ingestion, corrected analytics/evidence and scoped shared changes. Budget: focused first implementation; keep report ≤200 words.

Read AGENTS.md, tasks/briefs/backend-interfaces.md (frozen), docs/02-dataset.md and relevant source manuals/records. Use docs/contracts.md for SQL restrictions. Do not read the entire research transcript.

Writable: app/load.py, app/store.py, app/rules.py, app/reports.py, tests/test_store.py, tasks/reports/B1-data.md only. No other agents, dependencies or shared file edits.

Implement the frozen KnowledgeStore/load contract using stdlib SQLite. Preserve originals, transactional union/dedupe/collision rollback, source notes, report facts/checks/FTS, corrected views, scoped field/rule changes and private-safe read-only SQL. Include all required source attributes, typed metadata, real names/IDs. Report unknown formats; never skip critical rows silently. Be concise: no generic framework.

Acceptance: sample Q1/Q4/Q5/Q6/Q8/Q10 anchors via general queries; reload idempotence/collision preservation; Q12/Q13 field changes and T350 pump-jack-only rule scope; unsafe SQL rejected while corrected-view queries work. Write focused tests first, run python3 -m pytest tests/test_store.py -q. Evidence and rule refs must resolve, including report_file custom names. Missing provider is irrelevant.

Return one completion/blocker notification and report path. Do not mark global tasks complete. Ask Sol once for a necessary contract change rather than guessing.
