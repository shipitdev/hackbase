# Worker report: F0 — OpenUI compatibility spike

**Worker/model/effort:** GPT-6 Luna / medium (explicit assignment)
**Status:** P0 accepted by Sol; backend/browser integration pending
**Interface revision:** P0 in `docs/05-frontend-openui.md`

## Delivered

Added a narrow result-backed `AnswerLayout`, `ResultCard`, and `ResultTable` library in `frontend/src/genui/library.tsx`. It generates the prompt and schema from one library, binds literal result IDs/columns to supplied server-owned data, and delegates card/table UI to the published OpenUI widgets. Generated artifacts are under `frontend/src/genui/generated/`. The parser gate bounds input to 20,000 characters, explicitly checks IDs/titles/field names and selection counts, uses own-property result lookup, requires exactly one row for cards, and rejects invalid/excess props, unknown result columns, dynamic properties/functions, actions, queries, mutations, state, unresolved/orphaned/incomplete output, and dynamic roots. SSR asserts exact fictional fixture values and that hostile title/cell strings render escaped. No application data is embedded in the schema.

Pinned dependencies: `@openuidev/react-lang@1.0.1`, `@openuidev/react-ui@0.18.1`, `react@19.3.1`, `react-dom@19.3.1`, `zod@4.6.7`, `tsx@4.23.15`.

## Checks

| Command or manual check | Outcome | Evidence / exact failure |
|---|---|---|
| `npm run check:openui -- --write` | pass | Generated schema/prompt from the library. |
| `npm run check:openui` | pass | Valid parse; rejects malformed/dynamic programs, excess props, unknown columns/results, inherited result IDs, empty selections, multirow cards, and oversized input; SSR verifies exact values and escapes hostile text. |
| `npm ls --depth=0` | pass | All six pinned top-level packages resolve to the versions above. |
| `npm audit --json` | not completed | Registry request failed: `getaddrinfo ENOTFOUND registry.npmjs.org`; audit advisory status remains unknown. User reported 5 low findings from install; not fixed or re-audited. |

## Limits and decisions needed

The P0 gate proves parser metadata/tree validation and rendering compatibility, not FastAPI integration, user ownership enforcement, live model generation, or all six production visuals. The result binding is an isolated fixture harness. OpenUI package internals used by the proof are pinned; Sol should review before P1 adopts them.

## Handoff

Only assigned frontend package files, `frontend/src/genui/**`, `frontend/scripts/**`, and this report changed. Ready for Sol review.

## Sol acceptance

Reviewed package/library/guard code and requested additional bounds, own-key lookup, single-row card checks and escaping tests; worker implemented them. Root reran `npm run check:openui`: pass. Root audited the installed graph and traced five low findings to GHSA-238p-pmpm-9mq7 (KaTeX). Added a targeted katex0.18.2 override; install/audit reports0 vulnerabilities. OpenUI proof and a KaTeX render check pass after the override. No broad dependency upgrade or blind npm audit fix was applied.
