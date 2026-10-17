import json
from pathlib import Path

from app.load import load_dataset
from app.store import KnowledgeStore


DATASET = Path(__file__).parents[1] / "dataset/test-data/dataset"


def test_released_dataset_preserves_corrections_and_t500_rules(tmp_path):
    db = tmp_path / "release.sqlite"
    summary = load_dataset(DATASET, db)
    assert summary["counts"]["assets"] == 600
    assert not summary["collisions"]

    store = KnowledgeStore(db, analysis_date="2027-01-15")
    corrections = store.query_shared("""
        SELECT inspection_id, wellhead_temp_c, producing, payload
        FROM effective_inspections WHERE inspection_id='INS-0201-0218'
    """)["rows"]
    assert len(corrections) == 1
    row = corrections[0]
    assert row["wellhead_temp_c"] == 10.4
    assert json.loads(row["payload"])["wellhead_temp_c"] == 32.1

    rca = store.query_shared("""
        SELECT equipment_kind, value FROM effective_rules
        WHERE asset_id='WELL-0401' AND rule_key='rca_count'
        ORDER BY equipment_kind
    """)["rows"]
    assert {row["equipment_kind"]: row["value"] for row in rca}["esp_pump"] == 2
    assert {row["equipment_kind"]: row["value"] for row in rca}["flowline"] == 3

    asset = store.query_shared("""
        SELECT status, decommissioned_on, team_history, type_history
        FROM assets WHERE asset_id='WELL-0001'
    """)["rows"][0]
    assert {"status", "decommissioned_on", "team_history", "type_history"} <= asset.keys()
    late_inspection = store.query_shared("""
        SELECT recorded_at, inspected_at FROM effective_inspections
        WHERE recorded_at IS NOT NULL LIMIT 1
    """)["rows"]
    assert late_inspection and late_inspection[0]["recorded_at"]

