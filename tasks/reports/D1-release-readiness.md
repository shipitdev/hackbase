# Worker report: D1 — test dataset readiness

**Worker/model/effort:** GPT-6 worker; effort setting not exposed
**Status:** complete-for-review
**Interface revision:** current `load.load_dataset(root, knowledge_path)` contract

## Delivered

Added `scripts/preflight_dataset.py`, which reuses the checked loader in a new staging DB and can optionally SQLite-backup an existing shared knowledge DB first. It reports candidate and staged counts, version, duplicates, collisions, broken links and report coverage as JSON. Existing output paths and active knowledge/memory paths are refused; memory DB schemas are not accepted as snapshot sources. It never promotes data. Added focused tiny-fixture coverage for repeat loads, collisions preserving the base DB, and target protection. Added the release staging, backup, collision review and manual promotion runbook in `docs/released-data.md`. The released dataset has not arrived or been checked.

## Checks

| Command or manual check | Outcome | Evidence / exact failure |
|---|---|---|
| `pytest -q tests/test_preflight_dataset.py` | pass | 2 passed in 0.11s |
| `python3 scripts/preflight_dataset.py --help` | pass | CLI exposes positional `root`, optional `--base-db`, optional `--db` |
| Candidate release preflight | not run | Released dataset unavailable; no claim of release validation |

## Limits and decisions needed

The existing loader returns no structured broken-link list; it raises a checked error instead. Candidate-alone and merged staging outputs should both be reviewed. A real conflicting ID requires explicit source-owner policy before promotion.

## Handoff

Files no longer being edited: `scripts/preflight_dataset.py`, `tests/test_preflight_dataset.py`, `docs/released-data.md`, and this report. Reproduce with the two commands above. Promotion remains a deliberate, reviewed `python3 -m app.load <root> --db data/knowledge.sqlite` step.

**Sol review:** accepted after integration; see F6-final-sprint.md.
