"""Atomic, repeatable loader for a fleet/assets dataset root."""
import argparse
import hashlib
import json
import math
import sqlite3
from datetime import date, datetime
from pathlib import Path

from app.errors import AppError
from app.reports import extract_report
from app.rules import baseline_rules, read_rule_documents
from app.store import ensure_schema


def _json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AppError("invalid_request", f"Unreadable critical dataset file: {path}") from exc


def _jsonl(path):
    rows = []
    if not path.exists():
        return rows
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AppError("invalid_request", f"Malformed record at {path}:{number}") from exc
        if not isinstance(value, dict):
            raise AppError("invalid_request", f"Expected an object at {path}:{number}")
        rows.append(value)
    return rows


def _collect(root):
    root = Path(root).resolve()
    if not (root / "fleet").is_dir() or not (root / "assets").is_dir():
        raise AppError("invalid_request", "Dataset root must contain fleet/ and assets/")
    records = []
    def add(kind, row, source):
        key = {"asset": "asset_id", "inspection": "inspection_id", "maintenance": "maintenance_id", "regulatory_event": "event_id", "context": "note_id", "area": "area_id", "team": "team_id", "user": "user_id"}[kind]
        if not row.get(key):
            raise AppError("invalid_request", f"Missing {key} in {source}")
        records.append((kind, str(row[key]), row.get("asset_id", ""), json.dumps(row, sort_keys=True, separators=(",", ":")), str(Path(source).resolve().relative_to(root))))

    areas = _json(root / "fleet/areas.json")
    users = _json(root / "fleet/users.json")
    for row in areas.get("areas", []): add("area", row, root / "fleet/areas.json")
    for row in areas.get("teams", []): add("team", row, root / "fleet/areas.json")
    for row in users.get("users", []): add("user", row, root / "fleet/users.json")
    for folder in sorted((root / "assets").iterdir()):
        if not folder.is_dir(): continue
        meta_path = folder / "metadata.json"
        if not meta_path.exists(): raise AppError("invalid_request", f"Missing {meta_path}")
        metadata = _json(meta_path)
        if metadata.get("asset_id") != folder.name: raise AppError("invalid_request", f"Asset folder/id mismatch at {folder}")
        add("asset", metadata, meta_path)
        for filename, kind in (("inspections.jsonl", "inspection"), ("maintenance.jsonl", "maintenance"), ("regulatory-events.jsonl", "regulatory_event"), ("context.jsonl", "context")):
            for row in _jsonl(folder / filename):
                if row.get("asset_id") != metadata["asset_id"]: raise AppError("invalid_request", f"Wrong asset link in {folder / filename}")
                add(kind, row, folder / filename)
                if kind == "context" and row.get("note_type") == "correction" and row.get("inspection_id") and ("not a crude spill" in row.get("text", "").lower() or "not a spill" in row.get("text", "").lower()):
                    records.append(("source_correction", f"{row['inspection_id']}:spill_detected", metadata["asset_id"], json.dumps({"inspection_id":row["inspection_id"],"field":"spill_detected","value":False,"source_ref":row["note_id"]},sort_keys=True), str((folder / filename).relative_to(root))))
                if kind == "context" and row.get("note_type") == "data_correction":
                    field = row.get("field")
                    if field not in {"wellhead_temp_c", "ambient_temp_c", "spill_detected", "spill_est_volume_bbl"} or not row.get("inspection_id") or "corrected_value" not in row:
                        raise AppError("invalid_request", f"Invalid data correction in {row.get('note_id', folder)}")
                    records.append(("source_correction", f"{row['inspection_id']}:{field}", metadata["asset_id"], json.dumps({"inspection_id":row["inspection_id"],"field":field,"value":row["corrected_value"],"original_value":row.get("original_value"),"valid_from":row.get("valid_from"),"valid_to":row.get("valid_to"),"source_ref":row["note_id"]},sort_keys=True), str((folder / filename).relative_to(root))))
        for row in _jsonl(folder / "maintenance.jsonl"):
            filename = row.get("report_file")
            if not filename: continue
            report_path = (folder / filename).resolve()
            if not report_path.is_relative_to(folder.resolve()): raise AppError("invalid_request", f"Report path escapes asset directory: {filename}")
            report_id = row["maintenance_id"]
            try:
                text = report_path.read_text(encoding="utf-8")
                facts, checks = extract_report(report_id, metadata["asset_id"], str(report_path), text)
                records.append(("report", report_id, metadata["asset_id"], json.dumps({"title": f"Maintenance Report {report_id}", "asset_id": metadata["asset_id"], "text": text, "facts": facts, "checks": checks}, sort_keys=True), str(report_path.relative_to(root))))
            except (OSError, UnicodeError):
                records.append(("report", report_id, metadata["asset_id"], json.dumps({"title": f"Maintenance Report {report_id}", "asset_id": metadata["asset_id"], "text": "", "facts": [], "checks": [], "read_status": "unreadable"}), str(report_path.relative_to(root))))
    documents = read_rule_documents(root)
    for doc in documents:
        doc["path"] = str(Path(doc["path"]).relative_to(root))
        records.append(("document", doc["id"], "", json.dumps(doc, sort_keys=True), doc["path"]))
    # Repeated report rows are collected once per maintenance file reference.
    unique = {}
    for rec in records:
        identity = (rec[0], rec[1])
        if identity in unique and unique[identity][3] != rec[3]: raise AppError("invalid_request", f"Conflicting source rows for {identity}")
        unique[identity] = rec
    return list(unique.values()), baseline_rules(documents), {"assets": sum(x[0] == "asset" for x in unique.values()), "inspections": sum(x[0] == "inspection" for x in unique.values()), "maintenance": sum(x[0] == "maintenance" for x in unique.values()), "reports": sum(x[0] == "report" for x in unique.values()), "documents": len(documents)}


def _validate_merged(records):
    rows = {(kind,rid):json.loads(payload) for kind,rid,_,payload,_ in records}
    def ref(kind, value, owner):
        if value and (kind,value) not in rows: raise AppError("invalid_request",f"Broken {kind} reference {value} from {owner}")
        return rows.get((kind,value)) if value else None
    def numeric(value, owner, nonnegative=False):
        if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value) or (nonnegative and value<0):
            raise AppError("invalid_request",f"Invalid numeric value in {owner}")
    def iso(value, owner, with_time=False):
        try:
            if with_time:
                if not isinstance(value,str) or "T" not in value: raise ValueError
                datetime.fromisoformat(value.replace("Z","+00:00"))
            else: date.fromisoformat(value[:10])
        except (TypeError,ValueError,AttributeError) as exc: raise AppError("invalid_request",f"Invalid date in {owner}") from exc
    for (kind,rid),row in rows.items():
        owner=f"{kind} {rid}"
        if kind=="area":
            if not row.get("name"): raise AppError("invalid_request",f"Missing area name in {owner}")
            ref("team",row.get("team_id"),owner)
            center=row.get("center") or {}
            numeric(center.get("lat"),owner); numeric(center.get("lon"),owner)
            if not -90<=center["lat"]<=90 or not -180<=center["lon"]<=180: raise AppError("invalid_request",f"Invalid area center in {owner}")
        elif kind=="team":
            if not row.get("name"): raise AppError("invalid_request",f"Missing team name in {owner}")
        elif kind=="user":
            if not all(row.get(k) for k in ("name","role","team_id")): raise AppError("invalid_request",f"Missing user attributes in {owner}")
            ref("team",row["team_id"],owner)
        elif kind=="asset":
            for key in ("name","well_type","area_id","team_id","in_charge_user_id","installed_on"):
                if not row.get(key): raise AppError("invalid_request",f"Missing {key} in {owner}")
            iso(row["installed_on"],owner); ref("area",row["area_id"],owner); ref("team",row["team_id"],owner); ref("user",row["in_charge_user_id"],owner)
            location=row.get("location") or {}
            for key,low,high in (("lat",-90,90),("lon",-180,180)):
                numeric(location.get(key),owner)
                if not low<=location[key]<=high: raise AppError("invalid_request",f"Invalid {key} in {owner}")
            if not isinstance(row.get("equipment"),list) or not row["equipment"]: raise AppError("invalid_request",f"Missing equipment in {owner}")
            kinds=set()
            for item in row["equipment"]:
                if not isinstance(item,dict) or not all(isinstance(item.get(k),str) and item[k] for k in ("equipment_id","kind","model")) or item["kind"] in kinds: raise AppError("invalid_request",f"Invalid or duplicate equipment in {owner}")
                kinds.add(item["kind"])
            known_types={doc_id.removeprefix("OM-") for doc_kind,doc_id in rows if doc_kind=="document" and doc_id.startswith("OM-")}
            if row["well_type"] not in known_types: raise AppError("invalid_request",f"Unknown manual for {owner}")
        elif kind=="inspection":
            if not row.get("asset_id"): raise AppError("invalid_request",f"Missing asset_id in {owner}")
            if not row.get("inspection_id") or not row.get("method") or not row.get("inspector_user_id") or not isinstance(row.get("inspected_at"),str) or "T" not in row["inspected_at"]: raise AppError("invalid_request",f"Missing critical inspection attributes in {owner}")
            ref("asset",row["asset_id"],owner); ref("user",row["inspector_user_id"],owner); iso(row.get("inspected_at"),owner,True)
            for key in ("wellhead_temp_c","ambient_temp_c"):
                numeric(row.get(key),owner)
            if not isinstance(row.get("spill_detected"),bool): raise AppError("invalid_request",f"Invalid spill_detected in {owner}")
            for key in ("spill_area_pct","spill_est_volume_bbl"):
                if row.get(key) is not None:
                    numeric(row[key],owner,True)
                    if key=="spill_area_pct" and row[key]>100: raise AppError("invalid_request",f"Invalid spill_area_pct in {owner}")
        elif kind=="maintenance":
            ref("asset",row.get("asset_id"),owner); ref("user",row.get("technician_user_id"),owner); iso(row.get("started_at"),owner,True)
            if row.get("completed_at"): iso(row["completed_at"],owner,True)
            trigger=ref("inspection",row.get("triggered_by_inspection_id"),owner)
            if trigger and trigger.get("asset_id")!=row.get("asset_id"): raise AppError("invalid_request",f"Wrong inspection owner in {owner}")
            for value in (row.get("downtime_hours"), (row.get("cost_usd") or {}).get("total")):
                if value is not None: numeric(value,owner,True)
        elif kind=="regulatory_event":
            ref("asset",row.get("asset_id"),owner); iso(row.get("date"),owner)
            if row.get("fine_usd") is not None: numeric(row["fine_usd"],owner,True)
            trigger=ref("inspection",row.get("related_inspection_id"),owner)
            if trigger and trigger.get("asset_id")!=row.get("asset_id"): raise AppError("invalid_request",f"Wrong inspection owner in {owner}")
        elif kind=="context":
            if not isinstance(row.get("text"),str) or not row.get("note_type"): raise AppError("invalid_request",f"Missing note text/type in {owner}")
            ref("asset",row.get("asset_id"),owner); ref("user",row.get("author_user_id"),owner); iso(row.get("created_at"),owner,True)
            for key in ("valid_from","valid_to"):
                if row.get(key): iso(row[key],owner)
            trigger=ref("inspection",row.get("inspection_id"),owner)
            if trigger and trigger.get("asset_id")!=row.get("asset_id"): raise AppError("invalid_request",f"Wrong inspection owner in {owner}")
            if row.get("note_type")=="data_correction":
                field=row.get("field"); value=row.get("corrected_value")
                if field not in {"wellhead_temp_c","ambient_temp_c","spill_detected","spill_est_volume_bbl"} or not trigger or "original_value" not in row or "corrected_value" not in row:
                    raise AppError("invalid_request",f"Invalid data correction in {owner}")
                if field=="spill_detected":
                    if not isinstance(value,bool): raise AppError("invalid_request",f"Invalid data correction in {owner}")
                elif not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value) or (field=="spill_est_volume_bbl" and value<0):
                    raise AppError("invalid_request",f"Invalid data correction in {owner}")


def load_dataset(root, knowledge_path):
    records, rules, counts = _collect(root)
    path = Path(knowledge_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    duplicates = 0
    collisions = []
    try:
        ensure_schema(con)
        con.commit()
        con.execute("BEGIN IMMEDIATE")
        for rec in records:
            old = con.execute("SELECT asset_id,payload,source_path FROM raw_records WHERE kind=? AND record_id=?", rec[:2]).fetchone()
            if old:
                if (old[0], old[1]) != (rec[2], rec[3]):
                    collisions.append({"kind": rec[0], "id": rec[1]})
                else: duplicates += 1
            else:
                con.execute("INSERT INTO raw_records(kind,record_id,asset_id,payload,source_path) VALUES(?,?,?,?,?)", rec)
        if collisions:
            con.rollback()
            return {"counts": counts, "duplicates": duplicates, "collisions": collisions, "broken_links": [], "report_coverage": {"read": sum(r[0] == "report" and json.loads(r[3]).get("read_status") != "unreadable" for r in records), "unreadable": sum(r[0] == "report" and json.loads(r[3]).get("read_status") == "unreadable" for r in records)}}
        merged=con.execute("SELECT kind,record_id,asset_id,payload,source_path FROM raw_records").fetchall()
        _validate_merged(merged)
        for row in rules:
            key = (row["well_type"], row["rule_key"], row.get("equipment_kind", "*"))
            payload = json.dumps(row, sort_keys=True)
            old = con.execute("SELECT payload FROM baseline_rules WHERE well_type=? AND rule_key=? AND equipment_kind=?", key).fetchone()
            if old and old[0] != payload:
                collisions.append({"kind":"rule","id":"/".join(key)})
                continue
            if old: duplicates += 1
            else: con.execute("INSERT INTO baseline_rules(well_type,rule_key,equipment_kind,payload) VALUES(?,?,?,?)", (*key,payload))
        if collisions:
            con.rollback()
            return {"counts": counts, "duplicates": duplicates, "collisions": collisions, "broken_links": [], "report_coverage": {"read": sum(r[0] == "report" and json.loads(r[3]).get("read_status") != "unreadable" for r in records), "unreadable": sum(r[0] == "report" and json.loads(r[3]).get("read_status") == "unreadable" for r in records)}}
        con.execute("DELETE FROM docs_fts")
        for kind,record_id,payload in con.execute("SELECT kind,record_id,payload FROM raw_records WHERE kind IN ('document','report','context')"):
            doc=json.loads(payload)
            con.execute("INSERT INTO docs_fts(record_id,title,content) VALUES(?,?,?)",(record_id,doc.get("title",record_id),doc.get("content",doc.get("text",""))))
        digest = hashlib.sha256("\n".join(f"{r[0]}:{r[1]}:{r[2]}" for r in con.execute("SELECT kind,record_id,payload FROM raw_records ORDER BY kind,record_id")).encode()).hexdigest()[:12]
        digest = hashlib.sha256((digest+"\n"+"\n".join(r[0] for r in con.execute("SELECT payload FROM baseline_rules ORDER BY well_type,rule_key,equipment_kind"))).encode()).hexdigest()[:12]
        con.execute("INSERT INTO metadata(key,value) VALUES('dataset_version',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (f"{Path(root).name}-{digest}",))
        con.commit()
        return {"counts": counts, "duplicates": duplicates, "collisions": collisions, "broken_links": [], "report_coverage": {"read": sum(r[0] == "report" and json.loads(r[3]).get("read_status") != "unreadable" for r in records), "unreadable": sum(r[0] == "report" and json.loads(r[3]).get("read_status") == "unreadable" for r in records)}}
    except Exception:
        if con.in_transaction: con.rollback()
        raise
    finally:
        con.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("--db", required=True)
    args = parser.parse_args()
    summary=load_dataset(args.root, args.db)
    print(json.dumps(summary, indent=2))
    if summary["collisions"]: raise SystemExit(2)


if __name__ == "__main__": main()
