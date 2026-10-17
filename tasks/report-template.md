# Worker report: <task ID> — <lane>

Normally ≤200 words, excluding necessary log references. Send Sol the path and a short completion summary; do not duplicate the entire report in chat. Report blockers when intervention is needed, without waiting for a status request.

**Worker/model/effort:** <name and actual model/effort>
**Status:** complete-for-review | partial | blocked
**Interface revision:** <revision used>

## Delivered

<Concrete behavior, changed files and why. State if UI data was mocked.>

## Checks

| Command or manual check | Outcome | Evidence / exact failure |
|---|---|---|
| <command> | pass / fail / not run | <short result, count, log/artifact path> |

## Limits and decisions needed

<Remaining work, assumptions, known risks and any proposed contract change. Never claim an unrun check passed.>

## Handoff

<Files no longer being edited, how Sol can reproduce the result, and the next dependent action.>

**Sol review:** pending. Only the orchestrator accepts the task and updates the main checklist/state.
