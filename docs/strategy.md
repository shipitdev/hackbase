# Proposed design, in plain English

Use a React chat interface, a Python service and SQLite databases. The model decides which information it needs and how to present it. Ordinary code handles calculations, saved corrections and access to private history.

```text
User asks a question
    → app supplies relevant rules and permitted memory
    → model asks tools for records/calculations
    → database and document tools return results with sources
    → model describes the answer and the components to show
    → app checks that description and displays the actual result data
```

The build team uses Sol as the sole orchestrator and Luna workers; that development workflow is separate from the copilot’s runtime model. See [orchestration](orchestration.md), [system design](system-design.md) and [shared contracts](contracts.md).

The fourteen decisions below keep the earlier numbering so they can be compared with the original research. They describe the planned app, not completed work.

## D1. Keep the application small

Use FastAPI for the Python service and React/Vite for the browser. Give the model a small set of functions rather than adding an agent framework.

Allow up to eight model/tool rounds per answer, with time and output limits. Give a failed query one repair attempt. If the budget runs out, explain what was checked and what remains unanswered. Save tool results/errors for debugging under the requesting user.

## D2. Separate shared data from private chats

Use two SQLite files:

- `knowledge.sqlite`: wells, readings, repairs, reports, rules, shared notes and corrections.
- `memory.sqlite`: each user’s chats, previously discussed well lists and saved answer evidence.

The general query tool can read only approved shared data. Private history is read through a separate function that uses the user selected by the app. The model cannot choose a different user or attach the private database.

The user picker is sufficient for this local demo; it is not production login security.

## D3. Calculate with SQL; search documents by text

Use database queries for filters, totals, rankings and joins. Retrieve a report directly when its ID is known. Use SQLite’s built-in text search, FTS5, when searching by words.

No embeddings or vector database are needed. A keyword search can miss differently worded evidence, so a failed search alone does not prove nothing happened.

## D4. Give the model the small rulebook

The five manuals/SOPs total about 17KB. Include them, their headings and the database/tool instructions in the model’s working context. Do not include sample expected answers.

Keep the records outside the prompt until needed. Send relevant notes, a few report excerpts and the current user’s relevant history. Store long results and return a reference plus a useful preview, so they can be reopened.

Always preserve active corrections, disagreements, selected well lists and the latest question. Check a longer conversation too: a short successful demo does not prove later recall works. See [context guidance](04-genui-and-context.md).

## D5. Write down the rules the code calculates

Keep a short list of thresholds, deadlines and where each comes from. This includes the rule’s unit and who/what it applies to.

Check that list against the supplied documents when loading. If the rule text changes unexpectedly, flag it instead of calculating with an old value. Keep user-created rules separate and clearly attributed.

This is a small checked list, not a system that tries to turn arbitrary English into code.

## D6. Read report tables before asking a model

Save the full report text. Read every compliance-table row and extract clearly stated facts such as containment hours. Keep the exact supporting sentence or table row with each fact.

This covers all 616 real spills in the sample without asking a model to read all 1,509 reports. If a new report format cannot be read, mark the fact unknown and open the relevant report when answering. Do not treat a missing duration as zero or claim a complete result while relevant reports remain unread.

## D7. Apply corrections before every calculation

Never overwrite the original records. When answering, combine them with accepted corrections, then calculate status, spill class, deadlines and totals.

A temperature correction targets an inspection. A well/type rule can target a particular equipment kind. More specific applicable corrections take priority, but two conflicting corrections to the same target need visible resolution; do not quietly choose the newest. Keep the previously accepted value and show the unresolved proposal until clarified.

Count each inspection, repair or fine once even when several linked records exist. Do not save old calculated answers for reuse after corrections.

## D8. Give the model five clear tools

| Tool | What it does |
|---|---|
| `run_sql` | Runs a restricted read-only query and returns rows, column names and a result reference. |
| `get_evidence` | Opens a known record, report or rule section. |
| `search_documents` | Searches shared source reports/notes, with filters. |
| `memory_read` | Finds relevant history for the app’s selected user. |
| `remember` | Saves a checked shared note, field correction or scoped rule change. |

Enforce limits in application code. SQL cannot write, attach files, load extensions or read private chats. Normal queries use the corrected data; evidence lookup can show originals. Limit query time/output and say when returned rows are incomplete. Calculate totals before limiting displayed detail rows.

Bind authors on the server, validate targets/values, and prevent a retried write from saving the same correction twice. Save conversation turns automatically.

## D9. Save facts and discussion references differently

Shared notes save the well, author, text, dates and confirmation state. Corrections also save the field/rule, exact target, equipment kind where needed, original/new values and reason.

Private history saves messages, dates and exact well lists. For Q6, remember which three wells appeared; a vague summary is not enough for Q11. “Yesterday” uses conversation dates.

A clear correction can update a reading while still showing a conflicting inspector note, as Q12 requires. An ordinary “this well is running fine” claim is saved as context and does not change the temperature reading.

## D10. Show disagreements and uncertainty

Show who said what, when, and what the records indicate. Keep both sides; mark an unsupported claim unconfirmed and ask the user to clarify.

The answer can still reach a supported conclusion. In Q18, sampled crude supports “yes”, while the earlier produced-water opinion stays visible. Do not make a blanket rule that the latest speaker or an HSE role always wins.

Keep proven breaches, possible breaches, pending work, met/closed duties and unknown facts separate. Do not invent fines or closure. Preserve the Q9 source caveat in [the review](00-review.md).

## D11. Generate a combination of useful interface pieces

**Revision after the resource review and user choice:** let the model compose several components in OpenUI Lang, rather than allowing only one visual per answer.

For example, a well-status answer can contain a status card, a disagreement warning and expandable sources. A downtime comparison can contain a bar chart and a supporting table. The model chooses the relevant components, order, titles and data columns for each question.

**User-selected revision:** generate OpenUI Lang directly and render through OpenUI. Reuse its existing card/table/chart widgets through result-backed bindings; add map/heatmap support as needed. Prove parser, data binding and rendering compatibility before changing the backend response contract. Do not require OUI-1 or another paid UI service. [Native OpenUI plan](05-frontend-openui.md).

Reference stored query results instead of making the model copy chart numbers. Check allowed component names, columns and result ownership before rendering. No model-generated JavaScript or arbitrary HTML runs in the app.

Honor the requested visual. Include units, dates, zero values, chart legends, stopped-well markers and readable detail tables. Make sources and map points clickable. If rendering fails after one repair attempt, show the verified text and identify the missing visual.

## D12. Add new data without losing existing work

Load new records in one transaction: either the load succeeds, or the existing valid database stays unchanged. Ignore exact duplicates; add new IDs, including new history for known wells. Report differing records with the same ID and resolve their meaning explicitly.

Check required fields and links. Keep unknown extra fields, report unreadable document formats, and never silently omit bad rows from totals. Follow report paths safely within the asset folder.

Keep shared runtime corrections and private history when reloading. Print counts, errors and report-reading coverage. Keep the calculation date configurable, defaulting to 17 October 2026.

## D13. Use one working model and one fallback

Choose a provider already available to the builder. Verify tool use, a valid UI description and a correction flow; keep the initial provider check under ten minutes, preferably before the event.

Do not add a separate model for bulk report reading or UI generation. Record the model name, response time, usage and estimated cost where available. Test one fallback and make sure switching/retrying cannot repeat a saved change.

Provider access, limits, pricing and compatibility have not been checked by this review.

## D14. Make sources inspectable

Every factual answer points to the records and rules it used. The server checks references exist; clicking them opens the source. A source must support the specific statement beside it.

For a total or ranking, save the query, dates, data version, applied corrections and contributing records—or a way to reproduce that record list against the saved version. Show concise evidence in chat and expandable detail. Keep the question/result history private to its user.

A valid source ID alone does not prove the answer is right. Tests must compare the numbers and inspect what the sources actually say.

## What we are deliberately leaving out

Vector search, agent frameworks, model training/hosting, bulk model-based report reading, a generic rule compiler, saved-answer caching, image generation, enterprise authentication and deployment.

Remaining unknowns are the chosen provider and possible conflicting IDs/rules in the test dataset. All required visuals, corrections, memory and conflict behavior remain in scope.
