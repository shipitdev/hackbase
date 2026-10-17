# The data and the rules

Checked against `dataset/sample-data/` at commit `b8de8c9bd68f40334e5d06922126169e4f3bf3ca`. These counts describe the sample; the loader must not depend on them.

## What is in the sample

| Item | Count |
|---|---:|
| Wells / areas / users | 200 / 4 / 15 |
| Inspections | 39,567 |
| Repairs | 5,665: 4,156 scheduled, 1,509 corrective |
| Repair reports | 1,509 |
| Regulator events | 90 |
| Human notes | 141: 82 notes, 56 corrections, 3 feedback entries |
| Spill detections before corrections | 672; 1,466.0 barrels |
| Real spills after source corrections | 616; 1,352.3 barrels |

Inspection timestamps run from 20 October 2022 to 15 October 2026. The files total about 23.5MB. All five rule documents together are about 17KB.

## Where to find things

| Path under `sample-data/` | Contents |
|---|---|
| `fleet/areas.json` | Areas, teams and well membership |
| `fleet/users.json` | People and their roles |
| `fleet/well-types/` | T200 and T350 manuals |
| `fleet/sops/` | Spill, regulatory and field-work procedures |
| `assets/<well>/metadata.json` | Type, location, equipment and recorded status |
| `assets/<well>/inspections.jsonl` | Temperatures, spill estimates and inspector notes |
| `assets/<well>/maintenance.jsonl` | Repairs, costs, dates and report links |
| `assets/<well>/regulatory-events.jsonl` | Filed reports, notices, responses and fines |
| `assets/<well>/context.jsonl` | Notes and corrections |
| `assets/<well>/maintenance-reports/` | Full repair reports |

A `.jsonl` file has one JSON record per line.

Follow the inspection ID to related evidence: repairs use `triggered_by_inspection_id`, regulator events use `related_inspection_id`, and formal corrections use `inspection_id`. Other notes can mention an inspection only in their text.

Always follow a repair’s `report_file`, relative to that well’s directory. Names vary: MNT-0001-029 points to `MNT-0001-june-2026-flowline-spill.md`. All supplied report paths resolve. Three wells have no report directory; that is valid.

## Rules the app must apply

The manuals/SOPs are fictional challenge rules. T350 follows T200 except where its own manual replaces a rule.

| Rule | Plain meaning | Source |
|---|---|---|
| Producing oil | Wellhead minus air temperature ≥15°C for T200; ≥20°C for T350 | OM-T200 §9.3; OM-T350 §3 |
| High temperature | >85°C for T200 or >95°C for T350: shut in and inspect within 24 hours | OM-T200 §9.4; OM-T350 §4 |
| Spill area | >5% of pad area: shut in immediately until source repaired | OM-T200 §9.5; OM-T350 §5 |
| Planned shutdown | Record it in maintenance before work starts | OM-T200 §4; T350 inherits through §1 |
| Root-cause analysis | At least three corrective repairs on the same well/equipment kind in twelve months; investigate before the next repair closes | OM-T200 §10; OM-T350 §6 |
| Spill classes | Below 1 barrel: minor; 1–below 5: moderate; 5–below 25: reportable; 25 or more: major | SOP-SR §3 |
| Moderate spills | Notify HSE within 72 hours | SOP-SR §3 |
| SR-01 | Reportable/major: phone regulator immediately; written notice within 24 hours, or 2 hours for major | SOP-SR §4 |
| SR-02 | Stop source and contain within 4 hours of discovery | SOP-SR §4 |
| SR-03 | All spills: soil ≤1.0% TPH; haul soil >5% TPH. Reportable/major: at least four samples and passing agency verification within 60 days | SOP-SR §4 |
| SR-04 | Record every spill, including volume and area | SOP-SR §4 |
| RC-01 | Inspect at least every 14 days | SOP-RC §2 |
| RC-02 | Flowline integrity test once per calendar year | SOP-RC §2 |
| RC-03 | More than 14 consecutive days down: report to area supervisor | SOP-RC §2 |
| RC-04 | Answer a notice of violation within 30 days; track until closed | SOP-RC §2 |
| RC-05 | Maintain a flowline inspection, repair and cleanup program | SOP-RC §2 |
| WS-01 / WS-02 | Pre-job meeting; isolate energy before work | SOP-WS §3 |
| WS-03 | Personal H2S monitors; stop at ≥10ppm, move upwind; return only below 10ppm with HSE approval | SOP-WS §3 |
| WS-04 | Hot-work permit and gas test; no work at ≥10% LEL | SOP-WS §3 |
| WS-05 | Flowline repair pressure test: ≥1.25× maximum operating pressure, hold at least four hours without unexplained loss, before production | SOP-WS §3 |
| WS-06 | Contain oily waste; record quantity and manifest; use approved disposal | SOP-WS §3 |
| WS-07 | Write report within three days of finishing, with required work/safety/compliance details | SOP-WS §3 |

TPH is total petroleum hydrocarbons, the soil-cleanup measure. HSE is Health, Safety & Environment. A notice of violation is often shortened to NOV.

## Common mistakes to avoid

**Use the latest inspection, not the recorded status.** `recorded_status` refreshes monthly and can be stale. Find the latest timestamp from the actual inspections, not just the metadata pointer. Show people/areas/teams by name and wells by ID.

**Use corrected values consistently.** Keep originals, apply accepted corrections, then calculate. Round displayed values after calculations; check exact threshold boundaries carefully.

**Do not turn every note into a correction.** All 56 supplied correction notes cancel false spills, but future corrections can change temperatures or volumes instead. A note about counterweights or “I think it was water” does not change a numeric reading or threshold by itself.

**Respect dates.** Notes have `valid_from`/`valid_to`. A historical inspection’s correction still applies to that inspection when asked about it later. A future work plan is not a current outage.

**Repairs have no status column.** Compare start/completion dates to identify an ongoing job; a future completion may be planned. Even a finished repair does not prove production resumed: inspections govern that answer. Count costs by repair start date.

**Downtime is a challenge convention.** Each not-producing inspection adds seven days. Repair hours are separate. For RC-03, do not claim an uninterrupted outage across missed observations without supporting evidence; explain uncertainty.

## Reading reports and checking compliance

Save each report’s full text and links to its well, repair and triggering inspection. Read all compliance-table rows, including WS rules. Save extracted facts with their unit, source sentence/row and whether reading succeeded.

All 616 real sample spills have a readable containment duration in a report table. A narrow prose-only pattern misses the custom June report. There are 211 SR-02 failure rows and 102 reports with at least one WS failure.

An unreadable/missing fact is **unknown**, not zero or compliant. If relevant reports remain unread, say the result is incomplete.

A report’s old conclusion can become outdated after feedback. Q13’s report says “moderate”; corrected volume makes it reportable. Keep the measured 6.4-hour containment and soil result, but recheck reporting/verification duties. It records two samples; the new four-sample duty creates an action to check, not proof no later samples were taken.

Keep these distinctions:

- **Proven breach:** recorded failure, such as containment after seven hours.
- **Possible breach:** deadline passed and no supporting record found.
- **Pending:** future deadline or outstanding action.
- **Met/closed:** supporting evidence for that particular duty/action.
- **Unknown:** missing or unclear evidence.

Start spill deadlines at discovery, not repair start. Start the NOV-response deadline at the notice date. Match related events; do not count one fine several times through duplicate query rows. A closed filed report does not close a separate NOV. Agency cleanup verification requires a passing environmental site inspection. An annual test is not automatically overdue while the calendar year is unfinished.

Q9 has a recording-rule ambiguity; see [the review](00-review.md).

## Adding and reloading data

The planned loader takes a directory containing `fleet/` and `assets/`. It must:

1. Discover files and IDs; validate required fields, well ownership and links. Do not depend on 200 wells or fixed filenames.
2. Keep original JSON/text and source paths. Reject report paths escaping the well directory. Missing photo files are expected.
3. Add new records and ignore exact duplicates. If an existing ID has different data, report the conflict and leave the previous valid database unchanged. Check metadata, fleet definitions and rules too.
4. Preserve shared runtime notes, corrections and private chats on every reload.
5. Keep unknown extra fields. Fail clearly on malformed critical records; mark unfamiliar reports unread rather than silently removing them from totals.
6. Print counts, duplicates, conflicts, broken links and report-reading coverage. Re-read changed reports rather than reuse old extracted facts.

Treat the merged well records as the source of membership; an old fleet well list must not hide newly loaded assets. The test dataset’s exact overlap policy remains unknown. Do not guess if conflicting identities appear.
