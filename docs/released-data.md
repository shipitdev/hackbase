# Final dataset activation

Official release: repository commit `009e2b5`, `dataset/test-data/dataset/`.
Today is **15 January 2027**. The source contains 600 wells, seven areas, revised older records, new SOPs and 11 ordered final questions in `dataset/test-data/final-questions.md`.

The organizer and user explicitly require replacing the sample baseline. An append-only merge is inappropriate because older records were revised. Keep the official checkout unchanged.

1. Stop backend writers. Back up both SQLite stores together using SQLite backup; keep private backups out of Git.
2. Load the release into a fresh private staging database using `scripts/preflight_dataset.py`. Validate counts, source references, reports and rules.
3. Preserve accepted shared changes with their scope and provenance; review them against revised sources before transfer. Preserve the private memory database unchanged. Current activation found zero shared changes.
4. Promote the validated fresh knowledge database while writers are stopped, and increment `knowledge_revision` above the old value so saved sample results cannot be reused as current numbers. Keep old results as historical evidence.
5. Set `.env` `ANALYSIS_DATE=2027-01-15`, restart the backend, and verify health, counts, new wells and unchanged private memory.
6. Evaluate the final questions in order against an isolated snapshot. All evaluation sessions share that snapshot's knowledge and user-private memory. Save every turn's full response, visuals and errors privately; never overwrite the earlier sample evaluation.

Recovery point for this activation: `data/backups/before-final-20261017-164055/`. These ignored files contain private runtime data. The preflight command never activates data by itself. Historical sample tests retain their explicit 2026 dates.
