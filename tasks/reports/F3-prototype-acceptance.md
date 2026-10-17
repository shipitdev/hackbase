# F3 — orchestrator acceptance of chat prototype

17 October 2026. Sol reviewed Luna high F1 and Luna medium F2; both have returned file ownership. Native OpenUI v2 Card/Table chat is accepted as a prototype, not completion of six displays or all18 scenarios.

## Implemented

Real users/owned threads, new chat, persisted history, plain-text messages, native OpenUI renderer, source panel, conflicts/caveats, loading/errors and same-request retry. Sol integrated native result IDs into private recall, migrated API/integration/live-check fixtures, added Vite/strict TypeScript/startup docs and corrected the generated prompt's contradictory ban on static references. Original historical answers remain readable without rewriting them.

Requested taste-skill bundle installed with `npx skills add Leonxlnx/taste-skill`; lock records source. V2 excludes app screens, so original v1 typography/spacing/state guidance was adapted to the saved app layout. No marketing animations, external photos or added state/styling framework. Local skills are ignored.

## Evidence

- `python3 -m pytest -q`:78passed,48 upstream deprecation warnings,52.83s. Includes native tool/result/citation flow, ownership/revision checks, parser failures and private memory.
- `npm --prefix frontend run check:openui -- --write`:pass (generated prompt, official parser and SSR). Strict TypeScript exposed an existing assert overload; corrected its call without weakening assertion.
- `npm --prefix frontend run build`:pass. Logs remain ignored in data/checks/prototype-build.log. Upstream module-directive/large-bundle warnings remain; bundle optimization deferred.
- npm installation/audit:0 vulnerabilities.
- Actual browser → actual DigitalOcean: first request timed out; explicit manual Retry succeeded in64065ms, native Card+Table and7 sources. Original request ID reused,2 saved messages. `_check_answer` independently validates latest data/source/saved-result agreement:pass_with_limitations. Ignored owner-only snapshot:data/checks/native-browser-answer.json.
- Actual browser: manual-rule evidence opens through API, switching users clears previous visuals, switching back/reloading restores original history. No rendered visual errors. No console errors/warnings on final navigation.
- Mocked browser states (no paid calls): Card+Table, limitations/conflicts, original retry ID/no duplicate turns, changed text creates fresh request, selecting current chat preserves messages, closing pending evidence cannot reopen it, late private A answer ignored after switching to B, mobile drawer inert/focus/Escape. Native select consumes Escape on some platforms; Escape from another navigation control closes correctly.
- Actual responsive widths320/390/768/1440:no page overflow. Desktop/mobile screenshots visually inspected, ignored under data/checks/. Final mobile Send is unobstructed.

## Repairs and limits

OpenUI automatically mounts a CDN inspector in development, covering mobile Send. Its documented manual enabled=false did not suppress auto-mount in pinned1.0.1. A two-line pre-import bootstrap sets the package's existing auto-mount flag; browser verifies no host/toggle. This version-coupled shortcut is documented in source and must be checked on upgrades. No extra direct devtools dependency remains.

Not checked: full18 live scenarios, four remaining visual types, streaming, public deployment or production authentication. The UI is local demo user selection. Model latency/timeouts remain the main demo risk. No screenshots/runtime conversations/credentials are public artifacts.
