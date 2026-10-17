# B2 — Private conversation/results backend

Model: GPT-6 Luna high. Goal: persistent private threads, exact well-reference recall, result storage and request idempotency.

Read AGENTS.md and tasks/briefs/backend-interfaces.md (frozen), then only private-memory parts of docs/contracts.md and Q11/Q16 in docs/03-questions.md.

Writable: app/memory.py, tests/test_memory.py, tasks/reports/B2-memory.md only. No dependencies, other agents or other files.

Implement the frozen MemoryStore with stdlib SQLite and parameterized operations. All private lookups enforce selected user ownership. Keep messages, exact entity IDs, conversation timestamps and full results; bounded context previews may refer back to stored content. Persist request state and one user/assistant turn across retries. No frontend/model/network needed.

Acceptance: same-user new-thread recall finds earlier discussed IDs, another user cannot see them or results, restart retains state, repeated request returns identical cached answer, mismatched/in-progress requests reject safely, failed request retries do not duplicate turns, trace logs stay out of active context. Use a saved-result fixture matching SharedRows.

Write focused tests first; run python3 -m pytest tests/test_memory.py -q. Save a compact completion report with exact commands/outcomes and limits; notify Sol once when done or when a blocker needs intervention. Do not mark global tasks complete.
