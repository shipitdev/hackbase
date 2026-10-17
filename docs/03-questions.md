# The 18 example questions: what must work

The [official questions](../dataset/03-evaluation-queries.md) contain the full wording. The numbers below are checks for the sample data, not facts to put into the running app’s prompt or hardcode into answers.

Start each independent test from the original sample. Continue earlier corrections/history only where the question says to.

## Q1 — Current status of WELL-0001

Show a status card: **not producing**. Latest inspection INS-0001-0203 was on 15 October, by drone, by Ryan Brooks. Wellhead is 3.2°C above air, below T200’s 15°C threshold.

Explain Jake Morales’s planned shut-in note CTX-0001-003: rod-string work from 7 October, expected return around 20 October, not yet recorded in maintenance. The recorded `active` status is stale. Link the inspection, note and manual.

## Q2 — Stopped wells in Northeast Block 8

Show a table of four T200 wells, all last inspected on 15 October:

| Well | Temperature above air | Reason |
|---|---:|---|
| WELL-0164 | 4.1°C | No recorded cause; inspector says “Pump jack not moving.” |
| WELL-0170 | 2.9°C | Pump-jack repair MNT-0170-031 is ongoing |
| WELL-0172 | 5.7°C | Flowline repair MNT-0172-028 is ongoing |
| WELL-0175 | 0.4°C | No recorded cause |

Say when the cause is unknown and suggest a check. Do not invent one.

## Q3 — Thirteen weeks of temperatures

Show WELL-0001 wellhead and air temperatures as two lines: 13 readings, 23 July–15 October 2026. Mark **8 and 15 October** as not producing. Include inspection evidence and the temperature rule.

## Q4 — Four years of spills

WELL-0001 has **six spills totaling 15.1 barrels**. Show them in a table:

| Date | Barrels |
|---|---:|
| 16 March 2023 | 0.5 |
| 27 April 2023 | 2.6 |
| 28 September 2023 | 3.3 |
| 19 October 2023 | 0.3 |
| 11 June 2026 | 6.8 |
| 1 October 2026 | 1.6 |

There were seven detections. Exclude INS-0001-0070 using the rainwater correction CTX-0001-001. Cite included inspections too.

## Q5 — Downtime in 2025

Short answer: **21 days** for WELL-0001. Three inspections showed no production: INS-0001-0140 on 24 July, -0152 on 16 October and -0153 on 23 October. Each counts as seven days.

On 24 July, 51.6°C wellhead temperature was only 8.5°C above air. Explain the related repairs MNT-0001-021 and -023. Do not add repair hours.

## Q6 — Three wells with most downtime

Bar chart for Northeast Block 7, 16 June–16 October:

- WELL-0121: **49 days**.
- WELL-0138 and WELL-0107: **42 days each**.
- Next is WELL-0119 at 28 days.

Keep the tie; either stable tie order is fine. Save the exact three-well list privately for Michael’s later Q11. Retain contributing inspections and rules as evidence.

## Q7 — Map of real spills

Northeast Block 8, last 90 days: four pins with clickable details.

| Well | Date | Barrels | Latitude | Longitude |
|---|---|---:|---:|---:|
| WELL-0151 | 24 September | 4.5 | 32.12246 | -102.18445 |
| WELL-0165 | 30 July | 1.2 | 32.15665 | -102.14522 |
| WELL-0175 | 30 July | 3.9 | 32.18020 | -102.14790 |
| WELL-0186 | 23 July | 0.6 | 32.17552 | -102.17775 |

These are baseline values, before Q13. On new data, show one pin per well and list multiple spills if needed.

## Q8 — Spill heatmap

Count corrected spills by area and month. Show zero cells and human-readable area names.

| Area | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Southwest Block 23 | 4 | 3 | 3 | 6 | 3 | 4 | 4 | 3 | 3 | 2 | 35 |
| Southwest Block 24 | 7 | 4 | 5 | 6 | 5 | 5 | 3 | 1 | 5 | 2 | 43 |
| Northeast Block 7 | 5 | 3 | 2 | 4 | 6 | 6 | 2 | 4 | 4 | 1 | 37 |
| Northeast Block 8 | 4 | 4 | 4 | 3 | 2 | 4 | 4 | 0 | 1 | 0 | 26 |

Generate the month range from the question/calculation date; do not always hardcode January–October.

## Q9 — Broken rules and open actions

WELL-0001 has four breaches from the 11 June spill:

- SR-01: written notice after 41 hours, beyond 24 hours.
- SR-02: containment after about seven hours, beyond four.
- SR-03: verification overdue since 10 August.
- RC-04: NOV response overdue since 30 July.

The USD5,000 fine remains open. Separately show pending flowline RCA and missing shut-in recording. The annual flowline test was met on 7 March.

Use INS-0001-0185, REG-0001-001/-002/-003, the custom June report, MNT-0001-028/-029/-032 and October report, CTX-0001-003, and the governing rules. Follow `report_file` for the June report. See the [Q9 interpretation caveat](00-review.md).

## Q10 — Late containment

Southwest Block 24, last 90 days: table with **two spills** exceeding four hours.

| Well | Inspection | Report/repair | Containment |
|---|---|---|---:|
| WELL-0082 | INS-0082-0198 | MNT-0082-028 | About 7.1 hours |
| WELL-0100 | INS-0100-0196 | MNT-0100-034 | About 8.1 hours |

Cite the reports and SR-02. Repair duration is not containment time.

## Q11 — Remember a previous chat

Michael asks Q6 on Day 1. In a new chat on Day 2, he asks about repair costs this year for those three wells:

- WELL-0121: **USD25,794**.
- WELL-0138: **USD46,942**.
- WELL-0107: **USD5,176**.

Retrieve his saved well list. Sum `cost_usd.total` by repair start date; do not add labor/parts again. Keep calculation date separate from conversation dates.

## Q12 — Correct a temperature

Michael corrects INS-0164-0205 from **24.0 to 41.0°C** because the thermal gun was faulty and the crew remeasured. Keep the original, author and reason.

Air is 19.9°C, so the corrected difference is 21.1°C: WELL-0164 is producing. Also show Tyler’s conflicting “Pump jack not moving” note and ask Michael to confirm the disagreement. The explicit correction still applies.

Ask Q2 again: only WELL-0170/-0172/-0175 remain. Explain why WELL-0164 disappeared. Repeat in a new chat and after restart.

## Q13 — Correct a spill estimate

Michael changes INS-0151-0201 from **4.5 to 5.4 barrels**. It is now reportable:

- Written notice was due within 24 hours of 24 September, 15:30 UTC. None is recorded: flag a possible SR-01 breach.
- MNT-0151-025’s “moderate” classification and no-agency-verification conclusion are outdated.
- Its 6.4-hour containment was already an SR-02 failure.
- Agency verification is due **23 November 2026**, so it is not yet overdue.

Correct only that inspection. Keep the old estimate/report; do not invent a fine.

## Q14 — Change a rule for a well type

Baseline pump-jack RCA list for Northeast Block 7: **WELL-0108, WELL-0121, WELL-0138**, with three corrective repairs each.

Michael changes the rule to two repairs for **T350 pump jacks**. A new chat must add WELL-0120. WELL-0102 has two repairs but is T200 and stays excluded. Other equipment rules stay unchanged. Attribute the change to Michael, not the manual.

## Q15 — Another user sees the corrections

Continue Q12 and Q13. Jessica asks about WELL-0164: yes, producing, with Michael’s correction and the conflicting note visible.

Laura asks about reportable spills in Northeast Block 8, last 90 days: WELL-0151 only, corrected to 5.4 barrels, with no written notice recorded and the deadline passed. Share corrections without exposing unrelated private chat history.

## Q16 — Shared plan, private discussion

Jake shares WELL-0007’s planned workover from 17 October for about ten days. Michael in a new chat can see that plan and its author. It does not establish current downtime.

Jessica asks the Q11 wording. She has no such earlier discussion: do not use Michael’s three-well list.

## Q17 — A person disagrees with records

Michael says WELL-0175 has been shut in since 14 October. Tyler says it is running fine. Jessica’s 15 October inspection shows only 0.4°C above air: not producing, supporting Michael’s statement.

Keep both statements; mark Tyler’s unconfirmed and ask for clarification. Then Jake claims WELL-0001 has been online since 14 October. Its latest inspection and CTX-0001-003 disagree; save that claim as unconfirmed too. Neither casual claim changes a reading.

## Q18 — Two people disagree about a spill

For WELL-0101 on 20 August, INS-0101-0197 detected 1.0 barrel. Ryan’s CTX-0101-002 suggests produced water; Chris’s CTX-0101-003 reports sampled crude. Neither is a formal correction; MNT-0101-029 repaired the spill.

Answer **yes**, explain the sampling evidence and show both notes. Do not discard a note or cancel a spill just because an uncertain opinion mentions water.

## How to run the checks

Reset Q1–10 and Q18 to the original sample. Run Q6→Q11 with Michael and two conversation days. Test Q12, Q13 and Q14 separately, then combine Q12+Q13 for Q15. For Q16, give Michael the earlier history and Jessica none. Run Q17’s statements in order.

Check numbers, well sets, dates, saved corrections, sources, disagreements and requested visuals—not exact prose. Repeat representative checks after a new chat and reload.

Also check:

- Equality at thresholds, four-hour containment and exactly 5% spill area.
- Several linked repairs/events do not multiply counts or fines.
- Empty results and unreadable reports are stated honestly.
- A different well/area/date and a WS failure work without special question routing.
- Multiple generated components use the same correct data; source links open supporting records.
- Ten unrelated turns do not erase an earlier well list, and switching users does not expose it.
- Document text cannot trigger a saved change or switch users; SQL cannot read private history.
- Repeated loads do not duplicate data or erase corrections; conflicting records leave existing data intact.

Check visuals in a real browser. A valid interface description alone does not prove the chart, map or stopped-well markers actually appear. Photo references are not available image files.
