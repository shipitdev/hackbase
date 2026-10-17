"""Validate a candidate dataset in an isolated SQLite staging copy."""
import argparse
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.errors import AppError
from app.load import load_dataset


def _read_only(path):
    return f"{Path(path).as_uri()}?mode=ro"


def _version(path):
    with sqlite3.connect(_read_only(path), uri=True) as con:
        row = con.execute("SELECT value FROM metadata WHERE key='dataset_version'").fetchone()
        return row[0] if row else None


def _counts(path):
    with sqlite3.connect(_read_only(path), uri=True) as con:
        return dict(con.execute("SELECT kind, count(*) FROM raw_records GROUP BY kind"))


def _snapshot(source, target):
    with sqlite3.connect(_read_only(source), uri=True) as src:
        tables = {row[0] for row in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"raw_records", "metadata"}.issubset(tables):
            raise AppError("invalid_request", "Base database is not a shared knowledge database")
        with sqlite3.connect(target) as dst:
            src.backup(dst)


def preflight(root, *, base_db=None, db=None):
    project = Path(__file__).resolve().parents[1]
    active_paths = {(project / "data" / name).resolve() for name in ("knowledge.sqlite", "memory.sqlite")}
    if db is None:
        fd, name = tempfile.mkstemp(prefix="dataset-preflight-", suffix=".sqlite")
        os.close(fd)
        target = Path(name)
    else:
        target = Path(db).expanduser().resolve()
        if target in active_paths or target.exists():
            raise AppError("invalid_request", "Staging --db must be a new path outside the active data databases")
    target.parent.mkdir(parents=True, exist_ok=True)
    if db is not None:
        target.touch(mode=0o600, exist_ok=False)
    if base_db is not None:
        source = Path(base_db).expanduser().resolve()
        if not source.is_file() or source == target or source in active_paths and source.name == "memory.sqlite":
            raise AppError("invalid_request", "--base-db must be an existing shared knowledge database")
        _snapshot(source, target)
    try:
        before = _version(target) if base_db is not None else None
        loaded = load_dataset(root, target)
        counts = _counts(target)
        with sqlite3.connect(_read_only(target), uri=True) as con:
            coverage = con.execute("""SELECT
                sum(json_extract(payload,'$.read_status') IS NOT 'unreadable'),
                sum(json_extract(payload,'$.read_status') = 'unreadable')
                FROM raw_records WHERE kind='report'""").fetchone()
        return {
            "status": "failed" if loaded["collisions"] else "ready",
            "dataset_root": str(Path(root).resolve()),
            "staging_db": str(target),
            "dataset_version_before": before,
            "dataset_version": _version(target),
            "candidate_counts": loaded["counts"],
            "staged_record_counts": counts,
            "duplicates": loaded["duplicates"],
            "collisions": loaded["collisions"],
            "broken_links": loaded["broken_links"],
            "report_coverage": {"read": coverage[0] or 0, "unreadable": coverage[1] or 0},
        }
    except (sqlite3.Error, OSError) as exc:
        raise AppError("invalid_request", f"Preflight could not complete: {exc}") from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="candidate dataset root containing fleet/ and assets/")
    parser.add_argument("--base-db", help="optional shared knowledge DB to back up into staging first")
    parser.add_argument("--db", help="new staging DB path; defaults to a unique file in the system temp directory")
    args = parser.parse_args()
    try:
        summary = preflight(args.root, base_db=args.base_db, db=args.db)
        print(json.dumps(summary, indent=2))
        if summary["status"] != "ready":
            raise SystemExit(2)
    except AppError as exc:
        print(json.dumps({"status": "failed", "error": exc.message}, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
