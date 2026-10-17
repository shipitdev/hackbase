# System design — the application we will build

This is the implementation map for the [four-hour plan](../tasks/plan.md). [Strategy](strategy.md) explains the decisions; [contracts](contracts.md) fixes how the pieces connect. Editable drawings are in [diagrams](diagrams/README.md).

## The whole system

```text
Sample/test folders → checked loader → shared knowledge database
                                             ↑
Browser chat → Python API → model/tool loop → read-only analytics + evidence tools
                 │               │
                 │               └→ checked shared notes/corrections
                 └→ user-scoped memory functions → private chat/results database

Tool results → checked component description → browser cards/charts/tables/map
```

The model helps choose queries and presentation. Ordinary code owns calculations, permissions, persistence and the actual displayed values. Build-time Sol/Luna orchestration is described separately in [orchestration](orchestration.md).

## Components and intended files

| Component | Job | Intended files |
|---|---|---|
| Loader | Read sample/test roots, validate links, deduplicate, preserve originals and runtime state | `app/load.py` |
| Shared store | Tables, corrected query views, safe analytics and result evidence | `app/store.py` |
| Rule/report reader | Checked rule values, report facts with supporting text, text search | `app/rules.py`, `app/reports.py` |
| Private memory | Threads, messages, discussed well IDs, saved results and user-scoped reads | `app/memory.py` |
| Copilot | Model calls, five tools, bounded retries, answer/component checks | `app/agent.py`, `app/provider.py` |
| API assembly | Request validation, active user/thread checks, connect modules | `app/main.py`, `app/contracts.py` |
| Browser | Chat, user picker, generated components and inspectable evidence | `frontend/src/App.tsx`, `Visual.tsx`, `api.ts`, `types.ts`, `styles.css` |
| Checks | Calculations/loading, multi-user sequences, actual browser output | Focused files under `tests/`; browser checks |

Paths are planned, not scaffolding already generated. Only add a module when its task needs it. The orchestrator freezes names before workers implement against them.

## Storage and responsibility

**Shared knowledge, `data/knowledge.sqlite`:** assets/equipment, users/areas/teams, inspections, repairs, regulator events, source notes, raw documents, extracted facts, baseline rules, runtime shared claims and accepted overrides.

Keep source rows/text unchanged. Corrected views combine them with applicable overrides at read time. Production, spill classes, RCA eligibility and totals follow those corrected values. Save author, reason, target, dates and superseded correction where relevant. A plain user claim cannot become an override automatically.

**Private memory, `data/memory.sqlite`:** threads/messages, conversation dates, exact discussed well lists, tool traces, result rows and aggregate evidence. Every private lookup checks the app-selected user and thread/result ownership. The analytics SQL connection cannot attach this file.

A result is private even when its contributing source records are shared: revealing it could reveal what another user asked. Runtime files stay out of the public repository.

## One question, end to end

1. Browser sends selected user, owned thread, message and a unique request ID.
2. API validates them and stores the user turn. It pins calculations to 17 October 2026; conversation timestamps remain separate.
3. The copilot receives tool instructions, the small rulebook, relevant permitted history and shared context. Large records remain outside the prompt.
4. It calls `run_sql`, `get_evidence`, `search_documents`, `memory_read` or `remember`. The server validates every call and supplies the user identity itself.
5. Read tools return result references, previews, evidence and completeness information. Accepted writes commit before dependent reads; retries cannot repeat a write.
6. The model returns an explanation, evidence references, disagreements and an ordered list of allowed visual components.
7. Server checks component types/columns and reference ownership, attaches the exact saved rows and saves the final assistant turn/discussed IDs.
8. Browser displays the answer. Source clicks open actual evidence; component failure is visible rather than hidden behind a successful-looking text answer.

First version returns a complete JSON answer over HTTP. Show a pending state while waiting. Streaming is optional later if it helps; it is not a dependency for the demo.

## Domain calculations

One shared calculation path applies original data → accepted correction → derived value → applicable rule/deadline → total or presentation. Do not have separate UI-only status or compliance calculations.

Required foundations are the 15°C/20°C production rules, seven days per stopped inspection, corrected spill counts/volumes, reporting/containment/verification deadlines, same-equipment RCA and repair costs by start date. Read all compliance rows, including WS failures. Preserve report text and recompute conclusions affected by corrections.

Keep proven failure, possible missing-evidence failure, pending action and unknown distinct. The dataset guide and [rule notes](02-dataset.md) govern exact details; [the review](00-review.md) records Q9’s ambiguity.

## Generated interface

Use a component list with six data displays: card, table, line, bar, map and heatmap. Text explanation, disagreement notices and source details surround those displays. A bar chart and table can share the same result reference, guaranteeing the same underlying numbers.

The implemented backend still returns validated component JSON. The user selected a native OpenUI frontend: the next contract will carry model-generated OpenUI Lang with result-backed components, reuse existing OpenUI widgets, and add map/heatmap support. Validate this integration before migrating the live path. No generated executable code is allowed. See the [OpenUI plan](05-frontend-openui.md) and [layout](ui-layout.md).

## Loading new data

Accept dataset directories with `fleet/` and `assets/`. Validate and load atomically. Identical IDs/records deduplicate; new records append. Differing values under an existing ID, including metadata/rules, produce a collision report and leave the prior data active. Inspect/resolve an actual source-update policy when needed; do not silently guess.

Preserve shared feedback and private memory. Log counts, duplicates, broken references, rule changes and report-reading coverage. Unknown extra fields remain available; unreadable reports retain raw text and explicit incomplete status. No fixed well count, area membership or sample answer belongs in runtime code.

## Failure limits and checks

Read-only SQL has authorization, time/output limits and no extension/attachment access. An unsuccessful query gets one repair attempt. Limit the loop to eight model/tool rounds and an overall timeout; report verified partial work if exhausted.

Scope-check writes, keep request IDs to prevent duplication, validate citations/results and preserve disagreements. Treat document text as evidence rather than instructions. Test repeat loads, threshold equality, duplicate-join risk, correction cascades, private-memory rejection, longer recall and real browser rendering.

Public deployment, authentication infrastructure, vector search, model training and runtime multi-agent orchestration remain outside this build. Runtime model access is still a preflight dependency.
