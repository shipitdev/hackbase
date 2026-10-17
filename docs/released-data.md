# Candidate dataset release runbook

The released test dataset has not arrived or been checked. Use this process when it does. The preflight command only writes a new staging database; it never promotes data.

## Inspect and stage

1. Keep the received source immutable. Record its release location and inspect the directory tree, `fleet/areas.json`, `fleet/users.json`, each asset's `metadata.json` and JSONL files, well type manuals, SOPs, and referenced report files. Confirm the root contains `fleet/` and `assets/`. Do not edit source files to make validation pass.
2. Stop the app and any process that can write shared knowledge or private memory. Back up `data/knowledge.sqlite` and `data/memory.sqlite` with SQLite's backup API while writes are stopped, and record both backup paths. Keep these two backups together as one recovery point. Never pass the memory database to preflight.
3. Run the candidate alone first:

   ```sh
   python3 scripts/preflight_dataset.py /path/to/released-data --db /tmp/released-alone.sqlite
   ```

   Then compare it with a snapshot of current shared knowledge:

   ```sh
   python3 scripts/preflight_dataset.py /path/to/released-data --base-db data/knowledge.sqlite --db /tmp/released-merged.sqlite
   ```

   `--db` must be a new path. It refuses existing files and the active `data/knowledge.sqlite` and `data/memory.sqlite` paths. Without `--db`, it writes a uniquely named staging file under the system temporary directory and prints that path. A `ready` status and exit code 0 mean the loader accepted the candidate in staging. Exit code 2 means an ID/rule collision; exit code 1 means invalid input or a preflight error. Keep the JSON output with the release notes.

## Decide and promote

Review counts, dataset version, report coverage, duplicate counts, broken links and every collision against the official source. The loader rejects conflicting values under an existing ID and rolls back the candidate batch. Do not resolve conflicts by editing the old row or dropping accepted corrections. Have the source owner clarify whether each conflicting ID is a correction, a new version, or an erroneous release; record the decision and preserve original evidence. Re-run staging only after the source policy is explicit.

After review, stop writers again and confirm both recovery backups are intact. The existing loader's exact interface is:

```sh
python3 -m app.load /path/to/released-data --db data/knowledge.sqlite
```

This command is the deliberate promotion step; it appends valid new records and leaves `data/memory.sqlite` untouched. Run it only after review. It prints candidate counts, duplicates, collisions, broken links and report coverage; collision exit code is 2. Do not use a destructive file replacement to promote a candidate.

Restart the app only after a successful load. Check `/api/health` for the active version, compare shared record counts with the staged result, confirm a newly released well and one report-backed answer, and verify saved memory and accepted shared corrections still appear with their original scope. Save the command output and verification notes. If any count, correction, or memory check differs from the backups, stop and restore both databases from the same recovery point before serving answers.
