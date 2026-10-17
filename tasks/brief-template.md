# Worker brief: <task ID> — <one bounded outcome>

- **Model/effort:** GPT-6 Luna high or medium; explain any exception.
- **Owner / budget:** <worker name>, <time budget>.
- **Token allowance:** <if explicitly assigned; otherwise use the compact defaults>. Keep this brief normally ≤250 words; link relevant sections rather than copying them.
- **Goal:** <what the user can do after this slice>.
- **Allowed files:** <exact list; include report path>.
- **Read-only dependencies:** <owned by someone else; do not edit>.
- **Required context:** `AGENTS.md`, relevant contract sections and source/rule/question files.
- **Interface revision:** <revision in docs/contracts.md>; preserve these names/shapes.
- **Must preserve:** <originals, privacy, scope, shared-file ownership, etc.>.
- **Acceptance:** <up to three concrete outcomes>.
- **Checks:** <exact commands to run; note if a browser check belongs to Sol>.
- **Known limits/ambiguities:** <only those affecting this task>.
- **Report:** `tasks/reports/<task>-<lane>.md` using the report template.

Do not launch other agents or expand scope. Report a needed contract/ownership change before touching shared files. Return what changed, checks/results and unresolved issues; do not mark the main task done.

Notify Sol once when finished; report a blocker only if it needs intervention. No routine progress messages. Keep the completion report normally ≤200 words and reference detailed logs by path.
