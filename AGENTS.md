# Agent instructions — Asset Intelligence Copilot

## Who decides and what is authorized

GPT-6.1 Sol in the main session is the sole build orchestrator. It owns the plan, contracts, assignments, integration decisions and acceptance of completed work. Workers implement a bounded assignment and report back; they do not launch their own agents or redesign the system.

Current stage: backend implementation authorized by the user. Build backend only in this phase; keep frontend tasks pending. Follow assigned file ownership.

Use GPT-6 Luna **high** for data, calculations, report reading, feedback, memory and substantial debugging. Use Luna **medium** for well-specified UI components, small edits and documentation. These are initial choices to evaluate, not guarantees. Do not change the orchestrator model or automatically change the finished app’s runtime model.

## Read the right context

Every worker reads this file, its assignment, [contracts](docs/contracts.md) and the relevant part of [the system design](docs/system-design.md). Then read only the source files and question/rule sections needed for that task. Do not inherit the entire orchestrator transcript by default.

The main session starts/resumes from [state](tasks/state.md), [plan](tasks/plan.md), [checklist](tasks/todo.md) and [orchestration rules](docs/orchestration.md). Update the state after accepting work or changing a decision. Saved files, not remembered chat alone, carry the build forward.

The official files in `dataset/` define the challenge. `docs/` contains the reviewed interpretation. `opencode/docs/` is preserved research. If sources disagree, identify the difference; do not silently change requirements.

## Work without collisions

- Use completion/blocker notifications, not repeated status polling or “are you done?” messages. While workers run, do independent useful work or wait for their notification. Investigate only a reported blocker, tool failure or missed agreed deadline.
- Minimize tokens: send brief paths and relevant sections, not full transcripts or repeated documents. Workers send one compact completion report (normally ≤200 words), plus a blocker message only when intervention is needed. Save verbose logs to files and reference them.
- Do not repeat searches, dumps, reviews or tests without a new change, failure or unresolved risk. Keep required correctness/privacy checks; avoid duplicated ceremony.

- Work only in the assignment’s allowed files. Ask the orchestrator for a necessary ownership change; continue independent work while waiting.
- Shared contracts, root dependencies, `app/main.py`, global test configuration and plan/state files belong to the orchestrator unless explicitly assigned.
- No two workers edit the same file simultaneously. Check the assignment table before touching a shared file. Never revert someone else’s changes.
- Do not initialize repositories, commit, publish, install global tools or modify `dataset/`/`opencode/` unless assigned. The workspace has a nested dataset repo; it is not the application repo.
- Do not send messages outside this agent team or submit event artifacts without user authorization.

## Non-negotiable behavior

- Calculation date: **2026-10-17**. Conversation dates and planned-work dates are separate.
- Calculate production from temperature difference and downtime from inspections. Use the source manuals/SOPs, not outside oil-field rules.
- Keep originals and apply accepted corrections to later calculations for all users, only at their stated scope. T350 pump-jack feedback does not change T200 or other equipment.
- Shared well facts are distinct from private chats. Enforce private access in code; the model cannot choose a different user for memory reads.
- Preserve disagreements. A casual claim does not overwrite a reading. Unknown evidence is not zero or proof of compliance.
- Use saved query results for all chart/table numbers. Support all six visuals and requested component combinations. No arbitrary model-generated code runs in the browser.
- Never hardcode sample answers or route by evaluation question wording/IDs. Those values belong in tests only.
- Loading is repeatable and preserves memory. Do not silently skip bad critical records, overwrite conflicting IDs or discard feedback.
- Keep secrets and runtime conversations out of public artifacts.

## Finish and report

Make the smallest complete change that meets the assignment. Reuse existing patterns; do not add a framework or dependency without the orchestrator’s agreement. New meaningful logic needs a focused test; trivial text/style changes do not need artificial tests.

Run the assignment’s checks and report exact commands, outcomes and limitations using [the report template](tasks/report-template.md). Say when a check was not run. Do not mark the main checklist complete: the orchestrator reviews the changed code, reruns the important checks, then accepts it.

A worker report is evidence for review, not proof of completion. If a failure repeats, report the reproduction and suspected cause rather than weakening tests or patching sample outputs.
