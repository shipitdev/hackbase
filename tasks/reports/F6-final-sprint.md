# Final sprint — orchestrator acceptance

17 October 2026. F4 Luna medium, F5 Luna high and D1 Luna high returned all ownership. Sol reviewed code and integrated server validation, dependencies and browser checks. No paid model calls or full18 rerun.

## Accepted

- F4: viewport-bound grid/flex sizing, min-width/min-height shrink, conversation-only scroll, full-width generated views, internal horizontal scrolling, stable composer. Root kept reduced-motion CSS behavior and stopped mixed views being squeezed into three tiny columns.
- F5: six native OpenUI views with unchanged Card/Table signatures. OpenUI bar; multi-series SVG line for gaps/stopped markers and supporting table; Leaflet map dynamic import, resize/cleanup, popup, tile-error/table fallback; accessible heatmap zeros/unknowns. Parser guards unchanged. Root repaired stale line-array prompt example, added example parse proof, y-axis labels/fill correction and heatmap text contrast. Python validates every saved row (finite numeric columns, coordinates, booleans, unique heatmap cells) after ownership/revision checks.
- D1: existing loader reused in staging-only preflight, optional read-only backup of base knowledge, counts/coverage/collisions, active/existing paths rejected. Root retained reserved temporary files with0600 permissions and corrected active-path test. docs/released-data.md covers backup/review/promotion; no release or active database loaded.
- Submission/writeup.md draft captures observed architecture/limits; final results/license/video still pending.

## Verification

`python3 -m pytest tests/test_agent.py tests/test_openui.py tests/test_api.py tests/test_preflight_dataset.py -q`:44passed,40 upstream deprecation warnings,20.04s. New saved-row validation cases also passed12 focused checks during integration. No provider calls.

`npm --prefix frontend run check:openui`:pass, all six parser/SSR/bridge mappings, unsafe program rejection, zeros/unknowns/inactive, published examples parse. `npm --prefix frontend run build`:pass. npm install/audit reports0 vulnerabilities. Leaflet1.9.4 and types pinned.

Browser fixture:20columns,35rows,long unbroken values,all six views. Widths1440→1024→768→390→320→1440: body width matches viewport, height900, outer scroll0, composer visible, internal conversation scroll,6views,0visual errors. Line plot scrolls internally on narrow widths. Three map points, popup,8loaded tiles verified; blocked tile requests produce readable fallback and coordinate table, points remain, no JS errors. Desktop/mobile screenshots visually inspected under ignored data/checks/final-six-*.png. All fixtures clearly fictional; no benchmark answer embedded in app.

## Limits

Real model generation of the four new view types and final released questions has not been checked; provider timeouts remain unresolved. No released dataset has arrived in this slice. License, exported write-up, video and authorized submission remain outstanding. Original E1 runtime artifacts untouched. Source dataset/opencode and active knowledge/private memory were not modified by staging tests.

Final real saved-history resize check (no model call): two persisted messages rendered at320px and1440px, no body overflow or visual errors, composer visible. Backend restarted with final Python integration.
