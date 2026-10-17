# Four-hour build plan

**Status: backend implementation in progress; frontend pending.** GPT-6.1 Sol is the sole build orchestrator, with bounded GPT-6 Luna worker tasks. Use [the checklist](todo.md) for acceptance, [the system design](../docs/system-design.md) for implementation, and [orchestration rules](../docs/orchestration.md) for dispatch/review.

## What we are aiming to finish

A local chat app that calculates answers from the records, shows its sources, chooses and combines useful visuals, remembers shared facts and private discussions correctly, and loads the test data safely.

Keep calculations pinned to **16 October 2026**. Keep every required visual and memory behavior in scope. Report failures honestly rather than claiming unsupported answers.

## Where the time goes

| Task | Time from start | What should work by then |
|---|---|---|
| [T1](todo.md#t1-check-the-setup) | 0–10 minutes | Model/tool connection, local app and SQLite text search work. |
| [T2](todo.md#t2-answer-one-real-question) | 10–30 | Q1 runs through the UI with a card and clickable sources. |
| [T3](todo.md#t3-add-calculations-and-charts) | 30–45 | Downtime/spill questions, tables, line/bar charts and heatmaps work. Answers can combine components. |
| [T4](todo.md#t4-answer-from-reports-and-rules) | 45–55 | Q9/Q10 use report evidence and distinguish failures from pending/unknown items. |
| [T5](todo.md#t5-add-the-map) | 55–65 | Q7 shows four correct points and clickable details. |
| [T6](todo.md#t6-save-memory-and-corrections) | 65–90 | Private recall, temperature/volume corrections and scoped type rules work. |
| [T7](todo.md#t7-test-users-disagreements-and-longer-chats) | 90–110 | Different users see shared facts but cannot inherit private history; conflicts stay visible. |
| [T8](todo.md#t8-check-the-sample-build) | 110–120 | Sample app, reload checks and submission outline are ready. |
| [T9](todo.md#t9-load-the-released-test-data) | 120–140 | New data is loaded and checked without losing memory. |
| [T10](todo.md#t10-run-the-final-questions) | 140–195 | Final answers are saved with evidence and clear limitations. |
| [T11](todo.md#t11-prepare-the-submission) | 195–230 | Write-up, video and public licensed repository are ready. |
| [T12](todo.md#t12-submit-and-confirm) | 230–240 | OrganizerHQ submission is complete and links work. |

The last-two-hour windows are conditional on organizer release. If data/questions arrive later, keep the time reserved and use the wait for regressions/submission preparation; do not fill it with new features. Preserve the final packaging/submission buffer.

These are time budgets, not measured estimates. Test credentials and tools before the event if permitted. Do not spend the opening half-hour comparing models.

## Build in this order

T1 → T2 establishes one working path from question to answer. T3–T6 extend that same path with calculations, report evidence, maps and memory. T7 checks how those pieces work together; T8 makes the sample build ready for new data.

T9 depends on the organizer releasing the test set. T10 depends on successful loading and the final questions. T11 and T12 turn observed results into the required submission.

The product sequence stays the same, but separate implementation lanes can run in parallel once Sol freezes [the contracts](../docs/contracts.md). Two workers are the default. Sol coordinates and integrates; workers do not create their own agents.

| Window | Sol owns | Worker A | Worker B |
|---|---|---|---|
| 0–10 minutes | Freeze contracts, provider check, shared dependency/setup decisions | No dispatch until inputs/ownership are clear | No dispatch until inputs/ownership are clear |
| 10–30 | API/model integration and Q1 acceptance | Luna high: loader/corrected data for T2 | Luna medium: chat/card/source UI for T2 using clearly marked fixtures until connected |
| 30–65 | Accept calculation/report results; connect and browser-check | Luna high: T3 calculations, then T4 reports | Luna medium: T3 renderers, then T5 map |
| 65–90 | Define/write the API/tool integration and review correction behavior | Luna high: bounded T6 private/shared memory slice | Luna medium: correction/conflict UI and persistence display |
| 90–110 | Review/fix integration issues; accept scenarios | Luna high: T7 scenario checks or one isolated backend fix | Luna medium: browser/UI fixes in assigned files |
| 110–120 | T8 integrated checkpoint and baseline snapshot | Finish assigned blocker checks; return file ownership | Prepare submission outline or fix one isolated issue |
| 120–195 | T9/T10 test-data policy, final-question runs and result acceptance | Focused data/report fixes or independent checks | Focused UI fixes/results packaging |
| 195–240 | Review actual claims, video and submission with user | Documentation/results assistance as assigned | No new product features |

A third worker is optional for an independent, usually read-only check. Do not run a second writer against active worker files. Each dispatch is smaller than a whole lane: use [the brief](brief-template.md), assign exact files and ask for [a report](report-template.md). Only Sol accepts/checks off the main tasks.

Sol’s durable handoff is [tasks/state.md](state.md). Update it after every accepted slice and before a context reset. The current session’s context is helpful; it is not the only record of decisions.

## Important checkpoints

**Minute 30:** a real question must run all the way through. If it does not, fix that path before adding more features.

**Minute 65:** all six visual types should render. Use plain working components before spending time on styling. An unread report fact stays unknown.

**Minute 110:** finish shared/private memory and disagreement checks, including a longer chat. Stop exploring new dependencies.

**Minute 120:** have a working sample build and a repeatable loader. Keep a clean sample copy for independent tests so earlier corrections do not accidentally change later expected results.

**After release:** new data and final questions take priority. If report wording changes, improve the small reader or inspect the relevant reports. Do not start bulk model processing. If IDs conflict, resolve the source policy explicitly before using affected answers.

**Minute 195 onward:** prepare the submission; fix only blockers. Reserve the last ten minutes for the portal and broken links.

## How we will check it

Use small tests for calculations, report reading, corrections and repeated loading. Run the required multi-step user scenarios in [the question guide](../docs/03-questions.md). Check the actual browser output, including several components in one answer, evidence links and switching users.

Keep full results saved outside the model prompt. Test that an earlier well list survives ten unrelated turns and cannot be recalled by another user.

For final questions, save the prompt, user, calculation date, answer, visual, sources, model and any failure as each question runs. Do not leave all result capture until the end. After fixing a problem, rerun the checks affected by that change.

## Main risks

| Risk | Response |
|---|---|
| Model connection or UI output fails | Test it first; keep one working fallback. |
| A correction changes one display but leaves another wrong | Use the same corrected query results throughout; check all displayed components. |
| Report/rule wording changes | Keep full sources, show reading coverage and flag unknowns. |
| Private discussion appears for another user | Keep private storage separate; enforce selected user in code. |
| New data conflicts with existing IDs | Reject the conflicting load safely and report the exact issue. |
| Time runs out | Follow checkpoints and save the last 45 minutes for packaging/submission. |

## Choices at build start

Use an already accessible model that passes the opening check. Default application locations are `app/` and `frontend/`, with ignored runtime files in `data/`. Leave `dataset/` and `opencode/` intact.

Use the small JSON-based component description by default. OpenUI is optional if already familiar and tested before the event; do not add a dedicated UI model or protocol stack. See [the resource review](../docs/04-genui-and-context.md).

This revision follows the user’s orchestrator-led approach. The user subsequently authorized backend implementation first. This phase runs the data and private-memory lanes in parallel while Sol integrates the API/model loop. Live provider compatibility and the actual test dataset’s overlap rules remain unverified.

## Saved references

- [AGENTS.md](../AGENTS.md): instructions for every worker.
- [System design](../docs/system-design.md) and [contracts](../docs/contracts.md): how the application pieces connect.
- [UI layout](../docs/ui-layout.md) and [Excalidraw drawings](../docs/diagrams/README.md): editable visual reference.
- [State](state.md), [brief](brief-template.md) and [report](report-template.md): resumable dispatch and acceptance.
