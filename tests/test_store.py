import json
import math
import sqlite3
import shutil
from pathlib import Path

import pytest

from app.errors import AppError
from app.load import _validate_merged, load_dataset, main as load_main
from app.store import KnowledgeStore


SAMPLE = Path(__file__).parents[1] / "dataset" / "sample-data"


def make_store(tmp_path):
    db = tmp_path / "knowledge.sqlite"
    load_dataset(SAMPLE, db)
    # Historical source benchmarks use the synthetic dataset's original analysis date.
    return db, KnowledgeStore(db, analysis_date="2026-10-16")


def test_corrected_views_and_source_evidence(tmp_path):
    _, store = make_store(tmp_path)
    q1 = store.query_shared("SELECT inspection_id, asset_id, inspected_at, wellhead_temp_c, ambient_temp_c, producing FROM latest_inspections WHERE asset_id = ?", ["WELL-0001"])
    assert q1["rows"][0]["inspection_id"] == "INS-0001-0203"
    assert q1["rows"][0]["producing"] == 0

    q4 = store.query_shared("SELECT COUNT(*) AS spills, ROUND(SUM(spill_est_volume_bbl), 1) AS barrels FROM effective_inspections WHERE asset_id = ? AND spill_detected = 1 AND inspected_at >= ?", ["WELL-0001", "2022-10-16"])
    assert q4["rows"] == [{"spills": 6, "barrels": 15.1}]
    q5 = store.query_shared("SELECT SUM(CASE WHEN producing=0 THEN 7 ELSE 0 END) AS days FROM effective_inspections WHERE asset_id=? AND inspected_at>=? AND inspected_at<?", ["WELL-0001", "2025-01-01", "2026-01-01"])
    assert q5["rows"][0]["days"] == 21
    q6 = store.query_shared("SELECT i.asset_id,SUM(CASE WHEN i.producing=0 THEN 7 ELSE 0 END) days FROM effective_inspections i JOIN assets a USING(asset_id) WHERE a.area_id=? AND i.inspected_at>=? AND i.inspected_at<=? GROUP BY i.asset_id ORDER BY days DESC,i.asset_id LIMIT 4", ["NE-07", "2026-06-16", "2026-10-16"])
    assert [(r["asset_id"], r["days"]) for r in q6["rows"]] == [("WELL-0121", 49), ("WELL-0107", 42), ("WELL-0138", 42), ("WELL-0119", 28)]
    q8 = store.query_shared("WITH RECURSIVE months(m) AS (SELECT date(?,'start of year') UNION ALL SELECT date(m,'+1 month') FROM months WHERE m<date(?,'start of month')), counts AS (SELECT a.area_id,strftime('%Y-%m',i.inspected_at) m,COUNT(*) n FROM effective_inspections i JOIN assets a USING(asset_id) WHERE i.spill_detected=1 AND i.inspected_at>=date(?,'start of year') AND i.inspected_at<? GROUP BY a.area_id,m) SELECT a.name,months.m,COALESCE(counts.n,0) n FROM areas a CROSS JOIN months LEFT JOIN counts ON counts.area_id=a.area_id AND counts.m=strftime('%Y-%m',months.m)", ["2026-10-16","2026-10-16","2026-10-16","2026-10-17"])
    assert len(q8["rows"]) == 40 and sum(r["n"] for r in q8["rows"]) == 141 and any(r["n"] == 0 for r in q8["rows"])
    q10 = store.query_shared("SELECT report_id,value FROM report_facts WHERE asset_id=? AND fact_key='containment_hours' AND value>4", ["WELL-0082"])
    assert any(r["report_id"] == "MNT-0082-028" and r["value"] == 7.1 for r in q10["rows"])
    assert any(r["id"] == "MNT-0001-029" for r in store.search_documents("41 hours after detection", {"asset_id":"WELL-0001"})["matches"])

    refs = store.get_shared_evidence(["INS-0001-0203", "OM-T200#9.3", "MNT-0001-029"])
    by_id = {r["id"]: r for r in refs}
    assert "INS-0001-0203" in by_id and "OM-T200#9.3" in by_id
    assert "MNT-0001-029" in by_id and "MNT-0001-029#report" in by_id
    assert "contained about 7 hours" in by_id["MNT-0001-029#report"]["content"]
    assert store.get_shared_evidence(["OM-T350#3", "SOP-SR#4"])[1]["id"] == "SOP-SR#4"
    assert any(r["id"] == "CTX-0001-003" for r in store.search_documents("planned", {"asset_id":"WELL-0001"})["matches"])
    compliance = store.query_shared("SELECT rule_id,reported_result FROM report_checks WHERE report_id=? AND rule_id IN (?,?)", ["MNT-0075-032", "Manual §10", "HSE notice"])["rows"]
    assert {r["rule_id"] for r in compliance} == {"Manual §10", "HSE notice"}


def test_load_is_idempotent_and_collision_rolls_back(tmp_path, monkeypatch, capsys):
    db, store = make_store(tmp_path)
    before = store.info()["counts"]
    version = store.info()["dataset_version"]
    summary = load_dataset(SAMPLE, db)
    assert summary["duplicates"] > 0
    assert KnowledgeStore(db).info()["counts"] == before

    altered = tmp_path / "altered"
    shutil.copytree(SAMPLE, altered)
    # A partial next batch may link to an already loaded inspection.
    incremental = tmp_path / "incremental"
    (incremental / "fleet").mkdir(parents=True)
    (incremental / "assets/WELL-0001").mkdir(parents=True)
    shutil.copy(SAMPLE / "fleet/areas.json", incremental / "fleet/areas.json")
    shutil.copy(SAMPLE / "fleet/users.json", incremental / "fleet/users.json")
    shutil.copy(SAMPLE / "assets/WELL-0001/metadata.json", incremental / "assets/WELL-0001/metadata.json")
    (incremental / "assets/WELL-0001/context.jsonl").write_text(json.dumps({"note_id":"CTX-0001-TEST","asset_id":"WELL-0001","author_user_id":"U-101","note_type":"operator_feedback","created_at":"2026-10-16T00:00:00Z","inspection_id":"INS-0001-0203","text":"incremental linked note"})+"\n")
    assert not load_dataset(incremental, db)["collisions"]
    merged_version = KnowledgeStore(db).info()["dataset_version"]
    merged_counts = KnowledgeStore(db).info()["counts"]
    assert merged_version != version
    assert any(r["id"] == "CTX-0001-TEST" for r in KnowledgeStore(db).search_documents("incremental linked note", {"asset_id":"WELL-0001"})["matches"])

    meta = altered / "assets/WELL-0001/metadata.json"
    data = json.loads(meta.read_text())
    data["recorded_status"] = "collision"
    meta.write_text(json.dumps(data))
    collision = load_dataset(altered, db)
    assert collision["collisions"] == [{"kind": "asset", "id": "WELL-0001"}]
    assert KnowledgeStore(db).info()["counts"] == merged_counts
    assert KnowledgeStore(db).info()["dataset_version"] == merged_version
    monkeypatch.setattr("sys.argv", ["load", str(altered), "--db", str(db)])
    with pytest.raises(SystemExit) as error: load_main()
    assert error.value.code == 2
    assert json.loads(capsys.readouterr().out)["collisions"]


def test_rules_obey_analysis_date_and_well_scope(tmp_path):
    _, store = make_store(tmp_path)
    wells = store.query_shared("SELECT asset_id FROM assets WHERE well_type='T350' ORDER BY asset_id LIMIT 2")["rows"]
    assert len(wells) == 2
    store.apply_shared_change({"kind":"rule_override","scope":"well_type","target_id":"T350","field":"production_delta_c","value":27,"valid_to":"2026-10-15","reason":"Expired value"},"U-101","expired")
    store.apply_shared_change({"kind":"rule_override","scope":"well_type","target_id":"T350","field":"production_delta_c","value":22,"valid_from":"2026-10-16","reason":"Current type rule"},"U-101","type-current")
    store.apply_shared_change({"kind":"rule_override","scope":"well","target_id":wells[0]["asset_id"],"field":"production_delta_c","value":24,"valid_from":"2026-10-16","reason":"More specific well rule"},"U-101","well-current")
    rows=store.query_shared("SELECT asset_id,value,source_ref FROM effective_rules WHERE rule_key='production_delta_c' AND asset_id IN (?,?) ORDER BY asset_id",[wells[0]["asset_id"],wells[1]["asset_id"]])["rows"]
    assert rows[0]["value"] == 24 and rows[1]["value"] == 22
    assert rows[0]["source_ref"] == "change:CHG-well-current"
    assert store.get_shared_evidence([rows[0]["source_ref"]])[0]["metadata"]["reason"] == "More specific well rule"


def test_expired_measurement_override_is_not_applied(tmp_path):
    _, store = make_store(tmp_path)
    raw = store.query_shared("SELECT wellhead_temp_c FROM effective_inspections WHERE inspection_id=?", ["INS-0164-0205"])["rows"][0]["wellhead_temp_c"]
    store.apply_shared_change({"kind":"field_override","scope":"inspection","target_id":"INS-0164-0205","field":"wellhead_temp_c","value":41,"valid_to":"2026-10-15","reason":"Expired correction"},"U-101","expired-measurement")
    current = store.query_shared("SELECT wellhead_temp_c FROM effective_inspections WHERE inspection_id=?", ["INS-0164-0205"])["rows"][0]["wellhead_temp_c"]
    assert current == raw


def test_overlapping_changes_validation_and_temperature_precision(tmp_path):
    db, store = make_store(tmp_path)
    good={"kind":"field_override","scope":"inspection","target_id":"INS-0164-0205","field":"wellhead_temp_c","value":41,"valid_from":"2026-10-01","valid_to":"2026-10-20","reason":"Remeasured"}
    first=store.apply_shared_change(good,"U-101","interval-a")
    overlap={**good,"value":42,"valid_from":"2026-10-16","valid_to":"2026-10-31"}
    result=store.apply_shared_change(overlap,"U-101","interval-b")
    assert result["status"]=="pending_conflict" and result["conflicts"][0]["existing_change_id"]==first["change_id"]
    for value in (-1, float("inf"), float("nan")):
        with pytest.raises(AppError):
            store.apply_shared_change({"kind":"field_override","scope":"inspection","target_id":"INS-0151-0201","field":"spill_est_volume_bbl","value":value,"reason":"bad"},"U-101",f"bad-{value}")
    for value,equipment in ((2.5,"pump_jack"),(True,"pump_jack"),(2,"unknown")):
        with pytest.raises(AppError):
            store.apply_shared_change({"kind":"rule_override","scope":"well_type","target_id":"T350","field":"rca_count","equipment_kind":equipment,"value":value,"reason":"bad"},"U-101",f"rca-{value}-{equipment}")
    assert store.query_shared("SELECT temperature_producing(34.9,19.9,15) AS at_limit,temperature_producing(34.899,19.9,15) AS below_limit")["rows"] == [{"at_limit":1,"below_limit":0}]
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(store,"info",lambda: (_ for _ in ()).throw(AssertionError("query_shared must not scan counts")))
    assert store.query_shared("SELECT COUNT(*) n FROM assets")["rows"][0]["n"] == 200
    monkeypatch.undo()


def test_loader_rejects_malformed_critical_inspection(tmp_path):
    db, _ = make_store(tmp_path)
    con=sqlite3.connect(db)
    rows=con.execute("SELECT kind,record_id,asset_id,payload,source_path FROM raw_records").fetchall()
    con.close()
    changed=[]
    for kind,rid,asset,payload,source in rows:
        data=json.loads(payload)
        if kind=="inspection" and rid=="INS-0001-0203":
            data["wellhead_temp_c"]=float("nan")
            payload=json.dumps(data)
        changed.append((kind,rid,asset,payload,source))
    with pytest.raises(AppError): _validate_merged(changed)
    for kind_to_change, record_id, mutate in (
        ("asset", "WELL-0001", lambda row: row.update(installed_on="not-a-date")),
        ("asset", "WELL-0001", lambda row: row.update(equipment=["pump_jack"])),
        ("inspection", "INS-0001-0203", lambda row: row.update(inspected_at="not-a-date")),
    ):
        changed=[]
        for kind,rid,asset,payload,source in rows:
            data=json.loads(payload)
            if kind==kind_to_change and rid==record_id: mutate(data); payload=json.dumps(data)
            changed.append((kind,rid,asset,payload,source))
        with pytest.raises(AppError): _validate_merged(changed)


def test_scoped_shared_changes_and_sql_boundary(tmp_path):
    _, store = make_store(tmp_path)
    result = store.apply_shared_change({"kind": "field_override", "scope": "inspection", "target_id": "INS-0164-0205", "field": "wellhead_temp_c", "value": 41.0, "reason": "Remeasured after faulty gun"}, "U-101", "q12")
    assert result["status"] == "accepted"
    row = store.query_shared("SELECT wellhead_temp_c, producing FROM effective_inspections WHERE inspection_id = ?", ["INS-0164-0205"])["rows"][0]
    assert row["wellhead_temp_c"] == 41.0
    assert row["producing"] == 1
    store.apply_shared_change({"kind": "rule_override", "scope": "well_type", "target_id": "T350", "field": "rca_count", "equipment_kind": "pump_jack", "value": 2, "reason": "Updated policy"}, "U-101", "q14")
    rules = store.query_shared("SELECT value,source_ref FROM effective_rules WHERE well_type = ? AND rule_key = ? AND equipment_kind = ? LIMIT 1", ["T350", "rca_count", "pump_jack"])
    assert rules["rows"][0]["value"] == 2
    assert store.query_shared("SELECT value FROM effective_rules WHERE well_type = ? AND rule_key = ? AND equipment_kind = ? LIMIT 1", ["T200", "rca_count", "pump_jack"])["rows"][0]["value"] == 3
    assert store.get_shared_evidence([rules["rows"][0]["source_ref"]])[0]["id"] == rules["rows"][0]["source_ref"]

    for sql in ["DELETE FROM assets", "ATTACH DATABASE ':memory:' AS private", "SELECT * FROM raw_inspections", "PRAGMA database_list", "WITH users AS (SELECT * FROM raw_records) SELECT * FROM users", "WITH /*x*/ \"users\" AS (SELECT * FROM raw_records) SELECT * FROM \"users\"", "WITH 'users' AS (SELECT * FROM raw_records) SELECT * FROM 'users'"]:
        with pytest.raises(AppError):
            store.query_shared(sql)
    claim=store.apply_shared_change({"kind":"shared_claim","scope":"well","target_id":"WELL-0001","text":"Operator reports a recent pump sound change","reason":"Operator observation"},"U-101","claim-evidence")
    evidence=store.get_shared_evidence([f"change:{claim['change_id']}"])[0]
    assert evidence["content"] == "Operator reports a recent pump sound change"
    assert evidence["metadata"]["text"] == evidence["content"]

