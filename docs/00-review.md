# What changed from the earlier research

The main idea was right: use a database for calculations, read reports for explanations, keep corrections, and generate the right visual for each question. The changes below make that approach easier to build and harder to get wrong.

## Changes that matter

| Earlier idea or missing detail | Revised decision and reason |
|---|---|
| Ask a model to read all 1,509 reports during loading | Read their tables with ordinary code first. All 616 real sample spills have a linked report with a readable containment time. Keep the full text for unfamiliar formats. |
| Containment times are only in prose | They also appear in the reports’ compliance tables. They are missing from the JSON records, not from every table. |
| Calculate corrected values only when loading | Calculate them when answering. Otherwise, a new correction can leave old totals and status values behind. |
| Keep private chats in the same database that the model queries | Use a separate private-memory database. A forgotten user filter must not expose another person’s chat. |
| The T350 rule changes RCA for the whole well type | It changes **pump-jack RCA for T350**. Other equipment and T200 wells keep their existing rule. |
| SR-03 applies only to reportable spills | The cleanup target applies to smaller spills too. Agency verification and the minimum four samples apply to reportable/major spills. |
| Focus compliance checks on spills | Read all compliance rows. There are 102 reports with at least one WS safety/reporting failure; the manuals also have temperature and spill-area rules. |
| Automatically extract every rule and trust the result | Keep a short, checked list of rules with links to the source text. Flag changed or unfamiliar rule wording. |
| Skip bad records and keep loading | Do not silently omit records from totals. Load safely, report errors and keep the previous valid data if loading fails. |
| A conflict field or a citation ID guarantees honesty | Test the actual behavior. A valid ID can still support the wrong claim, and a conflict list can wrongly be empty. |
| One date controls everything | Keep the dataset’s “today”, conversation dates and planned-work dates separate. |
| Test the 18 questions in one growing chat state | Reset independent tests. Carry corrections/history forward only when the scenario requires it. |
| One visual per answer | Allow a short list of components: for example, a chart, a supporting table and a disagreement warning. See the [GenUI notes](04-genui-and-context.md). |
| Spend 30 minutes comparing models | Use an already available model and a short working check. Prefer doing this before the four-hour clock. |

## What we kept

Python, SQLite, a small set of tools, all five rule documents available to the model, and no vector database. Exact counts and sums belong in database queries. The model decides what to ask for and explains the result.

The earlier research correctly identified temperature differences, inspection-based downtime, false-spill corrections, stale recorded status and the two kinds of memory.

## Places where the source needs care

**Current calculation date:** use **17 October 2026**, as corrected by the user. The source review and expected answers below were checked against the repository’s earlier 16 October 2026 benchmark; date-sensitive results must be recalculated for 17 October. The earlier research mentioned a Google Doc saying 17 October, but that document was not supplied or verified.

**Q9 shut-in recording:** the manual requires recording before work starts. The note says work began on 7 October and is unrecorded, but the expected answer calls recording a pending action. Preserve that expected categorization and mention the missing record. Do not invent a grace period.

**RCA timing:** three corrective repairs trigger an investigation before the next repair closes. A count alone does not prove the investigation is already overdue. Show the outstanding action and its evidence.

**New dataset overlap:** the guide says to load it “alongside” the sample, but does not explain differing records with identical IDs. Add new records and ignore exact duplicates. Stop and report conflicting values rather than choosing silently; resolve the policy if a real conflict appears.

## What was checked

The initial review read all four research files, the five official top-level documents and all five rule documents. It scanned every sample record and all 1,509 reports.

The main expected numbers reproduced: Q4 spills, Q5 downtime, Q6 ranking, Q7 map points, every Q8 heatmap cell, Q10 containment results, Q11 costs and Q14 candidate sets. Additional checks confirmed Q3 readings/markers and Q12/Q13 source readings. Record IDs are unique within their record types; all supplied inspection links resolve to the correct well. All report paths resolve.

A narrow prose pattern found only 615 containment reports; reading the table also handles the custom June report and reaches all 616. That is why the full text must remain available.

The app, model provider, browser behavior and unseen dataset have not been tested. The later resource review is documented separately in [04-genui-and-context.md](04-genui-and-context.md).
