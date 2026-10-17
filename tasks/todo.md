# Build checklist

Backend implementation is underway; frontend and end-to-end model/browser acceptance remain pending. Only the Sol orchestrator ticks a task after reviewing the changes and checking its behavior. [Timing](plan.md) · [Design](../docs/strategy.md) · [Expected answers](../docs/03-questions.md).

Suggested filenames below describe the full build. The backend exists in app/; frontend work has not started. Keep each worker packet to a few owned files. A task can involve several lanes, but filenames are not permission for simultaneous edits. Read [AGENTS.md](../AGENTS.md), [contracts](../docs/contracts.md) and [ownership rules](../docs/orchestration.md) before dispatch.

Before T1, Sol records the contract revision, assignments and next action in [state](state.md). Workers use [briefs](brief-template.md), return [reports](report-template.md), and leave the main checklist to Sol.

## T1. Check the setup

**Needs:** nothing. **Likely files:** `requirements.txt`, `app/main.py`, `frontend/package.json`, `frontend/src/App.tsx`, `.gitignore`.

- [ ] Start the browser app/API, verify one real model tool call and valid UI description, test a fallback, and check SQLite FTS5 text search.
- [x] Keep secrets/runtime state out of version control and return clear provider errors from the API (frontend display pending).
- [ ] Check: real provider call and local startup; establish the focused-test command.

## T2. Answer one real question

**Needs:** T1. **Likely files:** `app/load.py`, `app/store.py`, `app/agent.py`, `frontend/src/App.tsx`, `tests/test_domain.py`.

- [ ] Load the records/rules, keep originals, apply source false-spill corrections and answer Q1 with a status card and clickable sources.
- [x] Restrict query tools: no writes, attached databases, private chats or arbitrary file reads. Return reusable result references for UI components.
- [ ] Check: load counts, exact temperature thresholds, latest inspection, Q1 in the browser and its inspection/manual/note links.

**Minute 30 checkpoint:** one real question works from model to tools to UI, without a special route for its wording/ID.

## T3. Add calculations and charts

**Needs:** T2. **Likely files:** `app/store.py`, `app/agent.py`, `frontend/src/Visual.tsx`, `frontend/src/App.tsx`, `tests/test_domain.py`.

- [ ] Answer Q2–6/Q8 correctly with tables, line/bar charts and heatmaps. Show dates, units, ties, zeros and stopped-well markers.
- [ ] Let the model combine a chart/table/source detail in one answer. All components use saved results; retain the contributing records for totals.
- [ ] Check: expected numbers, a case with several linked records, and real browser rendering. Ensure linked records do not duplicate counts.

## T4. Answer from reports and rules

**Needs:** T2. **Likely files:** `app/reports.py`, `app/load.py`, `app/store.py`, `app/agent.py`, `tests/test_domain.py`.

- [ ] Read report compliance rows and containment facts; answer Q9/Q10 with evidence, including the custom June filename.
- [ ] Make WS failures discoverable; distinguish breaches, pending actions and unknown facts. Recheck old conclusions after corrections.
- [ ] Check: containment reading covers 616/616 real sample spills, Q9/Q10 match, a WS failure is found, and unfamiliar report wording stays unknown rather than zero.

## T5. Add the map

**Needs:** T3. **Likely files:** `frontend/src/Visual.tsx`, `frontend/package.json`, `frontend/src/styles.css`.

- [ ] Show Q7’s four correct locations, clickable spill details and a readable detail table.
- [ ] Handle empty results and failed map tiles clearly; keep points/coordinates usable and give the map a visible size.
- [ ] Check: points/popups in the browser, empty data and tile failure.

**Minute 65 checkpoint:** all six required data displays work; report-based answers show evidence and uncertainty.

## T6. Save memory and corrections

**Needs:** T2–T4. **Likely files:** `app/memory.py`, `app/store.py`, `app/agent.py`, `app/main.py`, `tests/test_scenarios.py`.

- [ ] Make Q11 recall Michael’s exact saved well list in a new chat; keep conversation dates separate from calculation dates.
- [ ] Make Q12/Q13 update later calculations while preserving originals, author and reason. Apply Q14 only to T350 pump-jack RCA. Repeated requests do not save the same change twice.
- [ ] Check: isolated Q11–14 sequences, corrected status/reporting/deadlines, unchanged T200/other-equipment rules, and persistence after restart/reload.

## T7. Test users, disagreements and longer chats

**Needs:** T3–T6. **Likely files:** `app/memory.py`, `app/agent.py`, `frontend/src/App.tsx`, `tests/test_scenarios.py`, `tests/test_domain.py`.

- [ ] Pass Q15–18: shared corrections/plans reach others; private history does not. Show disagreements, including Q12’s corrected reading versus its inspector note.
- [x] Keep ordinary status claims from overwriting readings; server-bound identity and current-user quote checks restrict writes (scripted adversarial tests; live model pending).
- [ ] Check: user-switch scenarios, private-query rejection, rephrased questions and recall after ten unrelated turns. Verify saved full results remain retrievable without filling every prompt with them.

**Minute 110 checkpoint:** all 18 scenarios have a recorded pass/failure; fix important shared causes and stop dependency exploration.

## T8. Check the sample build

**Needs:** T7. **Likely files:** `tests/test_domain.py`, `README.md`, `LICENSE`, `submission/writeup.md`, `.gitignore`.

- [x] Repeated loading changes no totals; new records append; conflicting IDs leave existing data intact; feedback/history survive (backend regression tests).
- [ ] Prepare run instructions, license and write-up outline; exclude secrets/private state and keep a clean evaluation copy.
- [ ] Check: focused tests, frontend production build and browser checks for user switching, multiple components, sources and invalid visual descriptions.

## T9. Load the released test data

**Needs:** T8 and organizer release. **Likely files:** `submission/results.md`; source changes only for a demonstrated loading defect.

- [ ] Load new data, check counts/links/rule changes/report coverage, and preserve existing notes/corrections/history.
- [ ] Resolve differing-ID conflicts explicitly; never omit or overwrite them silently.
- [ ] Check: source versus loaded counts, one new well/report and representative status/total/correction questions.

## T10. Run the final questions

**Needs:** T9 and final-question release. **Likely files:** `submission/results.md` and focused tests; keep each fix small.

- [ ] Save every final answer or explicit failure immediately, including user, calculation date, visual, sources and model/usage information where available.
- [ ] Follow the requested scenario order; reset independent scenarios. Fix general causes without hardcoding answers.
- [ ] Check: numbers and source support; rerun affected tests after each fix.

## T11. Prepare the submission

**Needs:** T10. **Likely files/artifacts:** `submission/writeup.md`, exported write-up, video, `README.md`, `LICENSE`.

- [ ] Finish a readable 2–3 page write-up with actual design, models/cost, final answers and failures; record a narrated video of at most five minutes showing a real UI question.
- [ ] Publish the licensed repository and reproducible instructions without keys/private conversations.
- [ ] Check: exported pages, video playback/duration and public links. Describe implemented behavior, not just the planned design.

## T12. Submit and confirm

**Needs:** T11. **Likely changes:** portal submission and artifact links; no code work unless a blocker appears.

- [ ] Submit write-up/results, video and public repository through OrganizerHQ before the deadline.
- [ ] Check: submission receipt/status and every submitted link; keep the confirmation.

**Done:** the submission is accessible, and claimed results match what the app actually demonstrated.
