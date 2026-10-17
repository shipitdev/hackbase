# Frontend plan: native OpenUI generation

**Decision, 17 October 2026:** the user chose direct OpenUI Lang generation. This replaces the earlier plan to generate a JSON component list and translate it in the browser. Build a narrow integration first, then the complete chat interface. Existing source data, calculation rules, private memory and DigitalOcean model access stay in place.

**Execution status:** P0 has a provisional package manifest only. npm cannot resolve registry.npmjs.org in the agent workspace. Package versions, headless parsing and rendering are not verified. The backend real-question harness has two passing mocked checks; its live provider attempt failed. User-terminal follow-up commands are recorded in tasks/state.md.

## What the user sees

Keep the [saved layout](ui-layout.md): user and thread navigation on the left, conversation and generated answers in the middle, source details in a panel. The visible calculation date is 17 October 2026. An answer can combine a status card, chart, table, warning and sources. These are composed for the question, not fixed screens selected by question wording.

OpenUI handles parsing, component composition and rendering. Its existing cards, text, tables and charts save us from writing those widgets from scratch. It does not calculate well status, enforce private memory access or guarantee correct numbers. Those remain backend jobs. Pandas is not needed.

## The integration we will build

```text
Question → existing FastAPI copilot → existing five tools → saved query results
         → model writes OpenUI Lang + answer metadata
         → official OpenUI parser + existing result/citation validation
         → persist the accepted program and exact results
         → OpenUI Renderer in React → existing widgets + map/heatmap additions
```

Use `@openuidev/react-lang` for `Renderer`, schemas and the official parser, plus `@openuidev/react-ui` for reusable UI components. Keep DigitalOcean's working provider/router. OpenUI supports using a provider directly; adopting its toolkit does not require OUI-1, OpenUI Gateway, a Thesys account or a second model call just to produce the UI. We will not route requests through both DigitalOcean and another paid gateway.

Start with the renderer in our own small React/Vite chat shell. OpenUI's complete Agent Interface is optional, not the first dependency: its example expects a chat-stream adapter and separate history integration, whereas our API already owns user-scoped threads and returns a completed answer. This avoids creating a second source of conversation memory. Streaming is deferred until the complete validated response works.

## Native format, trusted data

The model writes the OpenUI program directly. It must not write React, HTML, JavaScript, copied chart values or arbitrary fetch URLs. A JSON HTTP envelope is still appropriate for metadata; that does not make the UI JSON-generated.

Proposed response additions:

- `ui_format: "openui-lang"`, `ui_version: 1`, `ui`: the model's OpenUI program.
- Keep `answer`, resolved citations, conflicts, limitations, analysis date, request/thread/message IDs, model and served models.
- Server-owned `results`: the exact saved rows/columns needed by the accepted program, with result IDs, query/source versions and completeness metadata.
- Retire the model-authored `components` list for the native path. Old stored answers retain their original format and can be labeled historical; do not rewrite their values or pretend they are OpenUI programs.

The exact field migration is frozen only after the first parser/renderer check succeeds. Do not duplicate the same UI in both OpenUI Lang and a model-authored JSON component manifest.

Expose result-backed component signatures, for example:

```text
root = AnswerLayout([status, detail])
status = ResultCard("R1", "Latest production state", ["asset_id", "producing"])
detail = ResultTable("R1", "Inspection detail", ["asset_id", "wellhead_temp_c", "ambient_temp_c"])
```

`R1` is an example placeholder. In real answers it must be a result ID issued by the server. The small result bindings look up server-owned data and pass it to the UI widgets. They are not another calculation engine or a way for the model to supply rows. Define/export the signatures once; use the same generated schema and prompt on server and client.

## Six required displays

| Requirement | Reuse | Small app-specific work |
|---|---|---|
| Status card | OpenUI card/text primitives | Resolve one result row; show units, observation date, threshold and corrections |
| Table | OpenUI table/column components | Resolve selected columns; preserve nulls, labels and row counts |
| Bar chart | OpenUI built-in chart | Resolve category/value columns; expose supporting table and ties |
| Line chart | OpenUI built-in chart if its API supports our requirements | Resolve time/series; verify stopped-reading markers and missing-value behavior in the first chart check |
| Map | Registered `ResultMap` backed by Leaflet | Coordinates, click details, attribution, keyboard-accessible coordinate table and tile-failure state |
| Heatmap | Registered `ResultHeatmap` using a small accessible grid/table | Rows/columns, explicit zero cells, legend and values available without relying on color |

The official analytics example confirms table/line/bar components. Map and heatmap are not assumed to be built in; their availability was not established in the checked docs. All six need thin data bindings even when the visual widget already exists. If a built-in line chart cannot mark stopped inspections, add one targeted chart extension; do not quietly drop the requirement or replace the whole rendering stack.

## Validation before publishing an answer

1. Export the OpenUI component schema and model prompt from the same library. Pin package versions in a lockfile after installation.
2. Use the official `createParser` with that schema. For the first implementation, invoke a small Node validator from FastAPI through stdin/stdout with a timeout and an output-size limit. This reuses the frontend's Node dependency; it is not a new network service or a handwritten language parser.
3. Reject unknown components, incomplete/unresolved programs, excess arguments, unsupported dynamic expressions, and unreachable UI fragments that hide unvalidated references. Do not treat “the renderer dropped it” as valid completion.
4. Permit only a static component tree in v1. Reject Query, Mutation, state declarations, function calls, dynamic root expressions and action programs. Disable these in the generated prompt and enforce the restriction in parsed output; prompt instructions alone are insufficient. Root/result bindings must be literal IDs and column names, with a maximum of six data views and bounded tree depth/size.
5. Walk the parsed tree and reuse existing result checks: selected user and thread ownership, current knowledge revision, column existence/types, numeric chart values, valid coordinates and completeness. Hydrate the exact result rows on the server.
6. Apply existing citation/claim/private-memory checks. The model cannot choose the active user. Source panels open through the existing ownership-checked evidence endpoint.
7. Allow one model repair using parser errors, within the existing overall call/time/context budget. On failure return an explicit partial answer; never execute generated code or silently call another paid service.

The first compatibility check must prove that the published parser can run headlessly under Node with an exported schema. Check evaluated tree/AST restrictions rather than searching the source with regexes. If that API does not expose enough information, stop this migration and report the specific limitation before designing a replacement. Do not weaken the trust boundary to get a pretty demo.

## Build order and ownership

| Slice | Owner | Exact scope and acceptance |
|---|---|---|
| P0: compatibility check | Luna medium; Sol reviews | Minimal frontend package, one result card + table schema, generated prompt/schema, official parser under Node, renderer/server-render check. Parse valid native output; reject invented row props and Query/Mutation. No full chat page yet. |
| P1: native backend contract | Sol or one Luna high worker with exclusive ownership | Add native UI envelope and parser bridge, reuse existing data/citation checks, preserve request retries/history; one scripted and one live real-question check. |
| P2: chat and evidence shell | Luna medium | User/thread selection, messages, composer, native Renderer, evidence panel, loading/error/partial states. No model keys or alternate memory store in browser. |
| P3: all six displays | One Luna medium worker | Complete result bindings, map, heatmap and stopped-reading markers. Browser-check combined chart/table and map details. |
| P4: acceptance | Sol | Real Q1, then all required display/memory/correction scenarios; check source links, user switching, resize/keyboard, persistence and malformed UI. |

Keep assignments small and disjoint. Workers report on completion; do not poll. Sol owns the frozen API, dependency choices and acceptance. Do not add another frontend state framework or chat protocol unless the initial slice demonstrates a concrete need.

## First compatibility check: concrete files

- `frontend/package.json` and lockfile: React, OpenUI packages, Zod and the smallest TypeScript runner needed for the proof.
- `frontend/src/genui/library.tsx`: result component definitions and immutable result context; no application data embedded in the schema.
- `frontend/scripts/check-openui.tsx`: generate schema/prompt, parse a known program, server-render its components and assert exact supplied values.
- Generated schema/prompt under `frontend/src/genui/generated/`; document how to regenerate and check drift.

This is a design, not a claim that dependencies have been installed or that an OpenUI interface has rendered. Local Node 22.19.0/npm 10.9.3 are present; OpenUI packages were not found in the npm cache. Network/package availability is a separate compatibility gate.

## Evidence and unresolved work

- [OpenUI overview](https://www.openui.com/docs/openui-lang/overview): roles of library, prompt, parser and renderer; direct provider use is supported.
- [Renderer](https://www.openui.com/docs/openui-lang/renderer): parser errors and React integration.
- [Component definitions](https://www.openui.com/docs/openui-lang/defining-components): reusable components, schemas and library extension.
- [Parser API](https://www.openui.com/docs/api-reference/react-lang): generated schema, parsed tree and extracted query/mutation/state information.
- [Conversational analytics example](https://www.openui.com/cookbooks/conversational-analytics): ready-made tables, line/bar charts and the complete chat-shell option. Its hosted Gateway/cloud-history setup is an example, not a requirement to replace our backend.
- [OUI-1 announcement](https://www.openui.com/blog/oui-1): a UI-specialized model; it is separate from adopting the OpenUI toolkit. No assumption that it is available through our DigitalOcean account.

Backend Q1 live acceptance is still open. The new harness exists, but its one live attempt returned provider_error. No broad evaluation result or browser rendering is claimed. A successful small router smoke proves tool connectivity, not domain correctness or native OpenUI generation quality.
