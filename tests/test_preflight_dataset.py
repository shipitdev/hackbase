import json
import shutil

import pytest

from scripts.preflight_dataset import preflight
from app.errors import AppError


def _candidate(root, *, name="Candidate Well"):
    (root / "fleet/well-types").mkdir(parents=True)
    (root / "fleet/sops").mkdir()
    (root / "assets/WELL-0001").mkdir(parents=True)
    sample = __import__("pathlib").Path(__file__).resolve().parents[1] / "dataset/sample-data"
    shutil.copy(sample / "fleet/areas.json", root / "fleet/areas.json")
    shutil.copy(sample / "fleet/users.json", root / "fleet/users.json")
    for path in (sample / "fleet/well-types").glob("*.md"):
        shutil.copy(path, root / "fleet/well-types" / path.name)
    for path in (sample / "fleet/sops").glob("*.md"):
        shutil.copy(path, root / "fleet/sops" / path.name)
    metadata = {
        "asset_id": "WELL-0001", "name": name, "well_type": "T200",
        "area_id": "SW-23", "team_id": "TEAM-SW", "in_charge_user_id": "U-101",
        "installed_on": "2013-03-25", "location": {"lat": 31.8, "lon": -102.5},
        "equipment": [{"equipment_id": "WELL-0001-PJ", "kind": "pump_jack", "model": "PJ-228"}],
    }
    (root / "assets/WELL-0001/metadata.json").write_text(json.dumps(metadata))
    for filename in ("inspections.jsonl", "maintenance.jsonl", "regulatory-events.jsonl", "context.jsonl"):
        (root / "assets/WELL-0001" / filename).write_text("")
    return root


def test_repeat_load_and_collision_leave_base_unchanged(tmp_path):
    first = _candidate(tmp_path / "first")
    staged = tmp_path / "staged.sqlite"
    initial = preflight(first, db=staged)
    assert initial["status"] == "ready"
    assert initial["candidate_counts"]["assets"] == 1
    assert initial["dataset_version"]

    repeated = preflight(first, base_db=staged, db=tmp_path / "repeat.sqlite")
    assert repeated["status"] == "ready"
    assert repeated["duplicates"] > 0
    assert repeated["dataset_version"] == initial["dataset_version"]

    conflict = _candidate(tmp_path / "conflict", name="Changed Well")
    result = preflight(conflict, base_db=staged, db=tmp_path / "conflict.sqlite")
    assert result["status"] == "failed"
    assert result["collisions"] == [{"kind": "asset", "id": "WELL-0001"}]
    assert preflight(first, base_db=staged, db=tmp_path / "after.sqlite")["dataset_version"] == initial["dataset_version"]


def test_refuses_existing_or_active_staging_target(tmp_path, monkeypatch):
    existing = tmp_path / "already.sqlite"
    existing.write_text("keep")
    with pytest.raises(AppError):
        preflight(tmp_path, db=existing)
    assert existing.read_text() == "keep"

    project = tmp_path / "project"
    active = project / "data/knowledge.sqlite"
    monkeypatch.setattr("scripts.preflight_dataset.__file__", str(project / "scripts/preflight_dataset.py"))
    with pytest.raises(AppError):
        preflight(tmp_path, db=active)


def test_default_staging_retains_private_reserved_temp_file(tmp_path):
    from pathlib import Path
    result = preflight(_candidate(tmp_path / "candidate"))
    path = Path(result["staging_db"])
    try:
        assert result["status"] == "ready"
        assert path.stat().st_mode & 0o777 == 0o600
    finally:
        path.unlink()
