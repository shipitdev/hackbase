"""Shared SQLite knowledge store with corrected, read-only analytics views."""
import json
import functools
import math
import re
import sqlite3
import time
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.errors import AppError

APPROVED = {"assets", "equipment", "areas", "teams", "users", "effective_inspections", "latest_inspections", "effective_rules", "maintenance", "regulatory_events", "source_notes", "shared_claims", "report_facts", "report_checks"}
MEASUREMENTS = {"wellhead_temp_c", "ambient_temp_c", "spill_detected", "spill_est_volume_bbl"}


def _is_producing(wellhead, ambient, threshold):
    if wellhead is None or ambient is None or threshold is None: return None
    try: return int(Decimal(str(wellhead))-Decimal(str(ambient))>=Decimal(str(threshold)))
    except InvalidOperation: return None


def _shadowed_ctes(sql):
    tokens=re.findall(r"--[^\n]*|/\*.*?\*/|'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|`[^`]*`|\[[^]]*\]|[A-Za-z_]\w*|[(),]",sql,re.S)
    tokens=[t for t in tokens if not t.startswith(("--","/*"))]
    def ident(token):
        if token.startswith(('"','`','[',"'")):
            closing = ']' if token.startswith('[') else token[0]
            return token[1:-1].replace(closing + closing, closing).lower()
        return token.lower()
    def word(token,value): return token.lower()==value
    found=set()
    for i,token in enumerate(tokens):
        if not word(token,"with"): continue
        j=i+1
        if j<len(tokens) and word(tokens[j],"recursive"): j+=1
        while j<len(tokens):
            name=ident(tokens[j]); j+=1
            if name in APPROVED: found.add(name)
            if j<len(tokens) and tokens[j]=="(":
                depth=1; j+=1
                while j<len(tokens) and depth:
                    depth += (tokens[j]=="(")-(tokens[j]==")"); j+=1
            if j>=len(tokens) or not word(tokens[j],"as"): break
            j+=1
            if j<len(tokens) and word(tokens[j],"not"): j+=2
            elif j<len(tokens) and word(tokens[j],"materialized"): j+=1
            if j>=len(tokens) or tokens[j]!="(": break
            depth=1; j+=1
            while j<len(tokens) and depth:
                depth += (tokens[j]=="(")-(tokens[j]==")"); j+=1
            if j>=len(tokens) or tokens[j]!=",": break
            j+=1
    return found


def ensure_schema(con):
    con.executescript("""
    CREATE TABLE IF NOT EXISTS raw_records(kind TEXT NOT NULL, record_id TEXT NOT NULL, asset_id TEXT NOT NULL, payload TEXT NOT NULL, source_path TEXT NOT NULL, PRIMARY KEY(kind,record_id));
    CREATE TABLE IF NOT EXISTS baseline_rules(well_type TEXT NOT NULL, rule_key TEXT NOT NULL, equipment_kind TEXT NOT NULL DEFAULT '*', payload TEXT NOT NULL, PRIMARY KEY(well_type,rule_key,equipment_kind));
    CREATE TABLE IF NOT EXISTS changes(change_id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL, author_id TEXT NOT NULL, kind TEXT NOT NULL, scope TEXT NOT NULL, target_id TEXT NOT NULL, field TEXT NOT NULL, value_json TEXT, reason TEXT NOT NULL, equipment_kind TEXT, valid_from TEXT, valid_to TEXT, text TEXT, supersedes_id TEXT, status TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(record_id UNINDEXED,title,content);
    DROP VIEW IF EXISTS latest_inspections;
    DROP VIEW IF EXISTS effective_inspections;
    DROP VIEW IF EXISTS effective_rules;
    DROP VIEW IF EXISTS report_checks;
    DROP VIEW IF EXISTS report_facts;
    DROP VIEW IF EXISTS shared_claims;
    DROP VIEW IF EXISTS source_notes;
    DROP VIEW IF EXISTS regulatory_events;
    DROP VIEW IF EXISTS maintenance;
    DROP VIEW IF EXISTS equipment;
    DROP VIEW IF EXISTS assets;
    DROP VIEW IF EXISTS areas;
    DROP VIEW IF EXISTS teams;
    DROP VIEW IF EXISTS users;
    CREATE VIEW IF NOT EXISTS assets AS SELECT record_id AS asset_id, json_extract(payload,'$.name') name, json_extract(payload,'$.well_type') well_type, json_extract(payload,'$.area_id') area_id, json_extract(payload,'$.team_id') team_id, json_extract(payload,'$.in_charge_user_id') in_charge_user_id, json_extract(payload,'$.location.lat') lat, json_extract(payload,'$.location.lon') lon, json_extract(payload,'$.installed_on') installed_on, json_extract(payload,'$.recorded_status') recorded_status, json_extract(payload,'$.status') status, json_extract(payload,'$.decommissioned_on') decommissioned_on, json_extract(payload,'$.team_history') team_history, json_extract(payload,'$.type_history') type_history, payload FROM raw_records WHERE kind='asset';
    CREATE VIEW IF NOT EXISTS equipment AS SELECT a.asset_id, json_extract(e.value,'$.equipment_id') equipment_id, json_extract(e.value,'$.kind') equipment_kind, json_extract(e.value,'$.model') model FROM assets a, json_each(a.payload,'$.equipment') e;
    CREATE VIEW IF NOT EXISTS areas AS SELECT record_id area_id,json_extract(payload,'$.name') name,json_extract(payload,'$.team_id') team_id,json_extract(payload,'$.center.lat') lat,json_extract(payload,'$.center.lon') lon,payload FROM raw_records WHERE kind='area';
    CREATE VIEW IF NOT EXISTS teams AS SELECT record_id team_id,json_extract(payload,'$.name') name,payload FROM raw_records WHERE kind='team';
    CREATE VIEW IF NOT EXISTS users AS SELECT record_id user_id,json_extract(payload,'$.name') name,json_extract(payload,'$.role') role,json_extract(payload,'$.team_id') team_id,payload FROM raw_records WHERE kind='user';
    CREATE VIEW IF NOT EXISTS effective_inspections AS SELECT json_extract(r.payload,'$.inspection_id') inspection_id,r.asset_id,json_extract(r.payload,'$.inspected_at') inspected_at,json_extract(r.payload,'$.recorded_at') recorded_at,json_extract(r.payload,'$.inspector_user_id') inspector_user_id,json_extract(r.payload,'$.method') method,
      COALESCE((SELECT json_extract(c.value_json,'$') FROM changes c WHERE c.kind='field_override' AND c.scope='inspection' AND c.target_id=json_extract(r.payload,'$.inspection_id') AND c.field='wellhead_temp_c' AND c.status='accepted' AND (c.valid_from IS NULL OR c.valid_from<=analysis_date()) AND (c.valid_to IS NULL OR c.valid_to>=analysis_date()) ORDER BY c.created_at DESC LIMIT 1),(SELECT json_extract(s.payload,'$.value') FROM raw_records s WHERE s.kind='source_correction' AND s.record_id IN (json_extract(r.payload,'$.inspection_id')||':wellhead_temp_c',json_extract(r.payload,'$.inspection_id')) AND json_extract(s.payload,'$.field')='wellhead_temp_c' AND (json_extract(s.payload,'$.valid_from') IS NULL OR json_extract(s.payload,'$.valid_from')<=analysis_date()) AND (json_extract(s.payload,'$.valid_to') IS NULL OR json_extract(s.payload,'$.valid_to')>=analysis_date()) LIMIT 1),json_extract(r.payload,'$.wellhead_temp_c')) wellhead_temp_c,
      COALESCE((SELECT json_extract(c.value_json,'$') FROM changes c WHERE c.kind='field_override' AND c.scope='inspection' AND c.target_id=json_extract(r.payload,'$.inspection_id') AND c.field='ambient_temp_c' AND c.status='accepted' AND (c.valid_from IS NULL OR c.valid_from<=analysis_date()) AND (c.valid_to IS NULL OR c.valid_to>=analysis_date()) ORDER BY c.created_at DESC LIMIT 1),(SELECT json_extract(s.payload,'$.value') FROM raw_records s WHERE s.kind='source_correction' AND s.record_id IN (json_extract(r.payload,'$.inspection_id')||':ambient_temp_c',json_extract(r.payload,'$.inspection_id')) AND json_extract(s.payload,'$.field')='ambient_temp_c' AND (json_extract(s.payload,'$.valid_from') IS NULL OR json_extract(s.payload,'$.valid_from')<=analysis_date()) AND (json_extract(s.payload,'$.valid_to') IS NULL OR json_extract(s.payload,'$.valid_to')>=analysis_date()) LIMIT 1),json_extract(r.payload,'$.ambient_temp_c')) ambient_temp_c,
      COALESCE((SELECT json_extract(c.value_json,'$') FROM changes c WHERE c.kind='field_override' AND c.scope='inspection' AND c.target_id=json_extract(r.payload,'$.inspection_id') AND c.field='spill_detected' AND c.status='accepted' AND (c.valid_from IS NULL OR c.valid_from<=analysis_date()) AND (c.valid_to IS NULL OR c.valid_to>=analysis_date()) ORDER BY c.created_at DESC LIMIT 1),(SELECT json_extract(s.payload,'$.value') FROM raw_records s WHERE s.kind='source_correction' AND s.record_id IN (json_extract(r.payload,'$.inspection_id')||':spill_detected',json_extract(r.payload,'$.inspection_id')) AND json_extract(s.payload,'$.field')='spill_detected' AND (json_extract(s.payload,'$.valid_from') IS NULL OR json_extract(s.payload,'$.valid_from')<=analysis_date()) AND (json_extract(s.payload,'$.valid_to') IS NULL OR json_extract(s.payload,'$.valid_to')>=analysis_date()) LIMIT 1),json_extract(r.payload,'$.spill_detected')) spill_detected,
      json_extract(r.payload,'$.spill_area_pct') spill_area_pct,
      COALESCE((SELECT json_extract(c.value_json,'$') FROM changes c WHERE c.kind='field_override' AND c.scope='inspection' AND c.target_id=json_extract(r.payload,'$.inspection_id') AND c.field='spill_est_volume_bbl' AND c.status='accepted' AND (c.valid_from IS NULL OR c.valid_from<=analysis_date()) AND (c.valid_to IS NULL OR c.valid_to>=analysis_date()) ORDER BY c.created_at DESC LIMIT 1),(SELECT json_extract(s.payload,'$.value') FROM raw_records s WHERE s.kind='source_correction' AND s.record_id IN (json_extract(r.payload,'$.inspection_id')||':spill_est_volume_bbl',json_extract(r.payload,'$.inspection_id')) AND json_extract(s.payload,'$.field')='spill_est_volume_bbl' AND (json_extract(s.payload,'$.valid_from') IS NULL OR json_extract(s.payload,'$.valid_from')<=analysis_date()) AND (json_extract(s.payload,'$.valid_to') IS NULL OR json_extract(s.payload,'$.valid_to')>=analysis_date()) LIMIT 1),json_extract(r.payload,'$.spill_est_volume_bbl')) spill_est_volume_bbl,
      json_extract(r.payload,'$.evidence_images') evidence_images,json_extract(r.payload,'$.notes') notes,
      CAST(json_extract(effective_rule_json(a.well_type,'production_delta_c','',a.asset_id),'$.value') AS REAL) production_threshold_c,
      temperature_producing(COALESCE((SELECT json_extract(c.value_json,'$') FROM changes c WHERE c.kind='field_override' AND c.scope='inspection' AND c.target_id=json_extract(r.payload,'$.inspection_id') AND c.field='wellhead_temp_c' AND c.status='accepted' AND (c.valid_from IS NULL OR c.valid_from<=analysis_date()) AND (c.valid_to IS NULL OR c.valid_to>=analysis_date()) ORDER BY c.created_at DESC LIMIT 1),(SELECT json_extract(s.payload,'$.value') FROM raw_records s WHERE s.kind='source_correction' AND s.record_id IN (json_extract(r.payload,'$.inspection_id')||':wellhead_temp_c',json_extract(r.payload,'$.inspection_id')) AND json_extract(s.payload,'$.field')='wellhead_temp_c' AND (json_extract(s.payload,'$.valid_from') IS NULL OR json_extract(s.payload,'$.valid_from')<=analysis_date()) AND (json_extract(s.payload,'$.valid_to') IS NULL OR json_extract(s.payload,'$.valid_to')>=analysis_date()) LIMIT 1),json_extract(r.payload,'$.wellhead_temp_c')),COALESCE((SELECT json_extract(c.value_json,'$') FROM changes c WHERE c.kind='field_override' AND c.scope='inspection' AND c.target_id=json_extract(r.payload,'$.inspection_id') AND c.field='ambient_temp_c' AND c.status='accepted' AND (c.valid_from IS NULL OR c.valid_from<=analysis_date()) AND (c.valid_to IS NULL OR c.valid_to>=analysis_date()) ORDER BY c.created_at DESC LIMIT 1),(SELECT json_extract(s.payload,'$.value') FROM raw_records s WHERE s.kind='source_correction' AND s.record_id IN (json_extract(r.payload,'$.inspection_id')||':ambient_temp_c',json_extract(r.payload,'$.inspection_id')) AND json_extract(s.payload,'$.field')='ambient_temp_c' AND (json_extract(s.payload,'$.valid_from') IS NULL OR json_extract(s.payload,'$.valid_from')<=analysis_date()) AND (json_extract(s.payload,'$.valid_to') IS NULL OR json_extract(s.payload,'$.valid_to')>=analysis_date()) LIMIT 1),json_extract(r.payload,'$.ambient_temp_c')),json_extract(effective_rule_json(a.well_type,'production_delta_c','',a.asset_id),'$.value')) producing,
      r.source_path,r.payload
      FROM raw_records r JOIN assets a ON a.asset_id=r.asset_id WHERE r.kind='inspection';
    CREATE VIEW IF NOT EXISTS latest_inspections AS SELECT * FROM (SELECT e.*,ROW_NUMBER() OVER(PARTITION BY asset_id ORDER BY inspected_at DESC,inspection_id DESC) rn FROM effective_inspections e) WHERE rn=1;
    CREATE VIEW IF NOT EXISTS effective_rules AS SELECT a.asset_id,a.well_type,k.rule_key,CASE WHEN k.rule_key='rca_count' THEN e.equipment_kind ELSE '' END equipment_kind,json_extract(effective_rule_json(a.well_type,k.rule_key,CASE WHEN k.rule_key='rca_count' THEN e.equipment_kind ELSE '' END,a.asset_id),'$.value') value,json_extract(effective_rule_json(a.well_type,k.rule_key,CASE WHEN k.rule_key='rca_count' THEN e.equipment_kind ELSE '' END,a.asset_id),'$.unit') unit,json_extract(effective_rule_json(a.well_type,k.rule_key,CASE WHEN k.rule_key='rca_count' THEN e.equipment_kind ELSE '' END,a.asset_id),'$.source_ref') source_ref,json_extract(effective_rule_json(a.well_type,k.rule_key,CASE WHEN k.rule_key='rca_count' THEN e.equipment_kind ELSE '' END,a.asset_id),'$.description') description,json_extract(effective_rule_json(a.well_type,k.rule_key,CASE WHEN k.rule_key='rca_count' THEN e.equipment_kind ELSE '' END,a.asset_id),'$.scope') scope,json_extract(effective_rule_json(a.well_type,k.rule_key,CASE WHEN k.rule_key='rca_count' THEN e.equipment_kind ELSE '' END,a.asset_id),'$.author_id') author_id,json_extract(effective_rule_json(a.well_type,k.rule_key,CASE WHEN k.rule_key='rca_count' THEN e.equipment_kind ELSE '' END,a.asset_id),'$.reason') reason FROM assets a CROSS JOIN (SELECT DISTINCT json_extract(payload,'$.rule_key') rule_key FROM baseline_rules) k LEFT JOIN equipment e ON e.asset_id=a.asset_id AND k.rule_key='rca_count' WHERE EXISTS(SELECT 1 FROM baseline_rules b WHERE b.rule_key=k.rule_key AND b.well_type IN(a.well_type,'*') AND (b.equipment_kind='*' OR b.equipment_kind=e.equipment_kind)) AND (k.rule_key!='rca_count' OR e.equipment_kind IS NOT NULL);
    CREATE VIEW IF NOT EXISTS maintenance AS SELECT record_id maintenance_id,asset_id,json_extract(payload,'$.started_at') started_at,json_extract(payload,'$.completed_at') completed_at,json_extract(payload,'$.recorded_at') recorded_at,json_extract(payload,'$.maintenance_type') maintenance_type,json_extract(payload,'$.equipment_kind') equipment_kind,json_extract(payload,'$.issue') issue,json_extract(payload,'$.action_taken') action_taken,json_extract(payload,'$.downtime_hours') downtime_hours,json_extract(payload,'$.cost_usd.total') cost_usd_total,json_extract(payload,'$.cost_revision') cost_revision,json_extract(payload,'$.triggered_by_inspection_id') triggered_by_inspection_id,json_extract(payload,'$.report_file') report_file,payload FROM raw_records WHERE kind='maintenance';
    CREATE VIEW IF NOT EXISTS regulatory_events AS SELECT record_id event_id,asset_id,json_extract(payload,'$.date') date,json_extract(payload,'$.agency') agency,json_extract(payload,'$.event_type') event_type,json_extract(payload,'$.protocol_id') protocol_id,json_extract(payload,'$.related_inspection_id') related_inspection_id,json_extract(payload,'$.detail') detail,json_extract(payload,'$.hours_to_report') hours_to_report,json_extract(payload,'$.fine_usd') fine_usd,json_extract(payload,'$.status') status,payload FROM raw_records WHERE kind='regulatory_event';
    CREATE VIEW IF NOT EXISTS source_notes AS SELECT record_id note_id,asset_id,json_extract(payload,'$.author_user_id') author_user_id,json_extract(payload,'$.note_type') note_type,json_extract(payload,'$.inspection_id') inspection_id,json_extract(payload,'$.created_at') created_at,json_extract(payload,'$.valid_from') valid_from,json_extract(payload,'$.valid_to') valid_to,json_extract(payload,'$.text') text,payload FROM raw_records WHERE kind='context';
    CREATE VIEW IF NOT EXISTS shared_claims AS SELECT change_id claim_id,target_id asset_id,author_id,text,reason,valid_from,valid_to,status FROM changes WHERE kind='shared_claim';
    CREATE VIEW IF NOT EXISTS report_facts AS SELECT json_extract(f.value,'$.fact_id') fact_id,r.record_id report_id,r.asset_id,json_extract(f.value,'$.fact_key') fact_key,json_extract(f.value,'$.value') value,json_extract(f.value,'$.unit') unit,json_extract(f.value,'$.source_text') source_text,json_extract(f.value,'$.read_status') read_status,r.source_path FROM raw_records r,json_each(r.payload,'$.facts') f WHERE r.kind='report';
    CREATE VIEW IF NOT EXISTS report_checks AS SELECT json_extract(f.value,'$.check_id') check_id,r.record_id report_id,r.asset_id,json_extract(f.value,'$.rule_id') rule_id,json_extract(f.value,'$.reported_result') reported_result,json_extract(f.value,'$.detail') detail,r.source_path FROM raw_records r,json_each(r.payload,'$.checks') f WHERE r.kind='report';
    """)
    con.execute("INSERT OR IGNORE INTO metadata VALUES('knowledge_revision','0')")


class SharedRows(dict):
    pass


class KnowledgeStore:
    def __init__(self, path, analysis_date="2026-10-17"):
        self.path = str(path)
        self.analysis_date = analysis_date
        con = sqlite3.connect(self.path)
        try: ensure_schema(con)
        finally: con.close()

    def _connect(self):
        con = sqlite3.connect(f"file:{Path(self.path).resolve()}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA query_only=ON")
        baselines = [json.loads(r[0]) for r in con.execute("SELECT payload FROM baseline_rules")]
        changes = [dict(r) for r in con.execute("SELECT change_id,author_id,scope,target_id,field,value_json,reason,equipment_kind,valid_from,valid_to FROM changes WHERE kind='rule_override' AND status='accepted'")]
        def as_of(value): return value is None or value <= self.analysis_date
        @functools.lru_cache(maxsize=None)
        def effective_rule(well_type, rule_key, equipment_kind, asset_id):
            choices=[]
            for rule in baselines:
                if rule.get("rule_key") != rule_key or rule.get("well_type") not in (well_type,"*"):
                    continue
                rule_equipment=rule.get("equipment_kind","")
                if rule_equipment not in ("*",equipment_kind): continue
                choices.append(((rule.get("well_type")==well_type,rule_equipment==equipment_kind),rule))
            if not choices: return None
            baseline=max(choices,key=lambda item:item[0])[1]
            matches=[]
            for change in changes:
                if change["field"]!=rule_key: continue
                if not as_of(change["valid_from"]) or (change["valid_to"] and change["valid_to"] < self.analysis_date): continue
                if change["scope"]=="well_type" and change["target_id"]!=well_type: continue
                if change["scope"]=="well" and change["target_id"]!=asset_id: continue
                if change["equipment_kind"] and change["equipment_kind"]!=equipment_kind: continue
                matches.append(change)
            if matches:
                winner=max(matches,key=lambda c:(c["scope"]=="well",c["valid_from"] or ""))
                value=json.loads(winner["value_json"])
                return json.dumps({**baseline,**value,"source_ref":f"change:{winner['change_id']}","scope":winner["scope"],"author_id":winner["author_id"],"reason":winner["reason"]})
            return json.dumps({**baseline,"scope":"baseline","author_id":None,"reason":None})
        con.create_function("effective_rule_json",4,effective_rule)
        con.create_function("temperature_producing",3,_is_producing)
        con.create_function("analysis_date",0,lambda:self.analysis_date)
        return con

    def info(self):
        con = self._connect()
        try:
            counts = {name: con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0] for name in ("assets", "equipment", "users", "effective_inspections", "maintenance", "regulatory_events", "source_notes", "report_facts", "report_checks")}
            get = lambda key, default: (lambda row: row[0] if row else default)(con.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone())
            return {"dataset_version": get("dataset_version", "unloaded"), "knowledge_revision": int(get("knowledge_revision", "0")), "analysis_date": self.analysis_date, "counts": counts}
        finally: con.close()

    def users(self):
        return self.query_shared("SELECT user_id,name,role,team_id FROM users ORDER BY user_id").get("rows", [])

    def schema_text(self):
        con = self._connect()
        try:
            lines=[]
            for name in sorted(APPROVED):
                cols=[r[1] for r in con.execute(f"PRAGMA table_info({name})")]
                lines.append(f"{name}({', '.join(cols)})")
            return "\n".join(lines)
        finally: con.close()

    def rules_text(self):
        docs=self.search_documents("", {"kind":"rule"})["matches"]
        return "\n\n".join(f"{d['id']} — {d['title']}\n{d['content']}" for d in docs)

    def query_shared(self, sql, params=None):
        if not isinstance(sql, str) or not sql.strip(): raise AppError("query_rejected", "SQL query is required")
        con=self._connect()
        dataset_version=(con.execute("SELECT value FROM metadata WHERE key='dataset_version'").fetchone() or ["unloaded"])[0]
        knowledge_revision=int((con.execute("SELECT value FROM metadata WHERE key='knowledge_revision'").fetchone() or ["0"])[0])
        shadowed=_shadowed_ctes(sql)
        functions={"abs","avg","count","date","datetime","julianday","max","min","strftime","substr","sum","total","lower","upper","round","coalesce","ifnull","nullif","cast","like","row_number","rank","dense_rank","lag","lead","first_value","last_value","json_extract","json_each","effective_rule_json","temperature_producing","analysis_date"}
        def auth(action,a,b,db,source):
            if action == sqlite3.SQLITE_RECURSIVE: return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_SELECT: return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_READ:
                if a in {"raw_records","changes","baseline_rules","json_each"} and source in APPROVED and source not in shadowed: return sqlite3.SQLITE_OK
                return sqlite3.SQLITE_OK if a in APPROVED else sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_FUNCTION: return sqlite3.SQLITE_OK if (b or a or "").lower() in functions else sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_DENY
        con.set_authorizer(auth)
        deadline=time.monotonic()+2
        con.set_progress_handler(lambda: int(time.monotonic()>deadline), 1000)
        try:
            cur=con.execute(sql, params or [])
            names=[d[0] for d in cur.description or []]
            rows=cur.fetchmany(1001)
            if len(rows)>1000: rows=rows[:1000]; truncated=True
            else: truncated=False
            data=[dict(zip(names,row)) for row in rows]
            refs=set()
            for row in data:
                for value in row.values():
                    if isinstance(value,str) and re.fullmatch(r"(?:INS|MNT|REG|CTX)-[A-Z0-9-]+",value): refs.add(value)
                    elif isinstance(value,str) and value.startswith("change:CHG-"): refs.add(value)
            units={"wellhead_temp_c":"°C","ambient_temp_c":"°C","production_threshold_c":"°C","spill_est_volume_bbl":"barrels","spill_area_pct":"%","downtime_hours":"hours","cost_usd_total":"USD","containment_hours":"hours","soil_tph_pct":"% TPH","lat":"degrees","lon":"degrees"}
            booleans={"producing","spill_detected"}
            columns=[]
            for name in names:
                values=[row.get(name) for row in data if row.get(name) is not None]
                typ="boolean" if name in booleans else "integer" if values and all(isinstance(v,int) and not isinstance(v,bool) for v in values) else "number" if values and all(isinstance(v,(int,float)) for v in values) else "text" if values else "unknown"
                columns.append({"name":name,"type":typ,"label":name.replace('_',' ').title(),"unit":units.get(name)})
            return SharedRows(columns=columns,rows=data,returned_rows=len(data),total_rows=None,truncated=truncated,complete=not truncated,limitations=["Result truncated at 1000 rows"] if truncated else [],evidence_refs=sorted(refs),analysis_date=self.analysis_date,dataset_version=dataset_version,knowledge_revision=knowledge_revision,query={"sql":sql,"params":params or []})
        except AppError: raise
        except sqlite3.Error as exc:
            if "interrupted" in str(exc).lower(): raise AppError("timeout", "Shared query exceeded its time limit") from exc
            raise AppError("query_rejected", "Query rejected: " + re.sub(r"\b(?:/[^ ]+)+", "[path]", str(exc))) from exc
        finally: con.close()

    def get_shared_evidence(self, refs):
        con=self._connect(); out=[]
        try:
            for ref in refs:
                if not isinstance(ref,str): raise AppError("not_found","Unknown evidence reference",404)
                if "#" in ref:
                    if ref.endswith("#report"):
                        report_id=ref[:-7]
                        row=con.execute("SELECT asset_id,payload,source_path FROM raw_records WHERE kind='report' AND record_id=?",(report_id,)).fetchone()
                        if row:
                            out.append({"id":ref,"kind":"maintenance_report","title":f"Maintenance Report {report_id}","source_path":row[2],"content":json.loads(row[1]).get("text",""),"metadata":{"asset_id":row[0],"maintenance_id":report_id}}); continue
                    doc_id,section=ref.split("#",1)
                    row=con.execute("SELECT payload,source_path FROM raw_records WHERE kind='document' AND record_id=?",(doc_id,)).fetchone()
                    if row:
                        doc=json.loads(row[0]); found=next((s for s in doc.get("sections",[]) if s["id"]==ref),None)
                        if found: out.append({"id":ref,"kind":"document_section","title":found["heading"],"source_path":row[1],"content":found["content"]}); continue
                row=con.execute("SELECT kind,asset_id,payload,source_path FROM raw_records WHERE record_id=? AND kind NOT IN ('report','source_correction') ORDER BY CASE kind WHEN 'maintenance' THEN 0 ELSE 1 END LIMIT 1",(ref,)).fetchone()
                if row:
                    content=json.loads(row[2]) if row[0] not in {"document"} else json.loads(row[2])
                    out.append({"id":ref,"kind":row[0],"title":ref,"source_path":row[3],"content":content,"metadata":{"asset_id":row[1]}})
                    report=con.execute("SELECT payload,source_path FROM raw_records WHERE kind='report' AND record_id=?",(ref,)).fetchone()
                    if report:
                        out.append({"id":f"{ref}#report","kind":"maintenance_report","title":f"Maintenance Report {ref}","source_path":report[1],"content":json.loads(report[0]).get("text",""),"metadata":{"asset_id":row[1],"maintenance_id":ref}})
                    continue
                change_ref=ref.removeprefix("change:")
                change=con.execute("SELECT change_id,kind,target_id,author_id,reason,value_json,status,created_at,text FROM changes WHERE change_id=?",(change_ref,)).fetchone()
                if change:
                    claim_text=change[8] if change[1]=="shared_claim" else None
                    out.append({"id":ref,"kind":change[1],"title":ref,"source_path":"runtime shared knowledge","content":claim_text or change[4],"metadata":{"target_id":change[2],"author_id":change[3],"reason":change[4],"text":claim_text,"value":json.loads(change[5]) if change[5] else None,"status":change[6],"created_at":change[7]}}); continue
                raise AppError("not_found",f"Unknown evidence reference: {ref}",404)
            return out
        finally: con.close()

    def search_documents(self, query, filters=None):
        con=self._connect(); matches=[]; filters=filters or {}; terms=[x for x in query.lower().split() if x]
        try:
            fts_terms=[re.sub(r'[^\w-]', '', term) for term in terms]
            fts_terms=[term for term in fts_terms if term]
            if fts_terms:
                match = " AND ".join('"' + term + '"' for term in fts_terms)
                ids = {r[0] for r in con.execute("SELECT record_id FROM docs_fts WHERE docs_fts MATCH ?", (match,))}
            else: ids = None
            rows=con.execute("SELECT record_id,payload,source_path,kind FROM raw_records WHERE kind IN ('document','report','context')").fetchall()
            for row in rows:
                if ids is not None and row[0] not in ids: continue
                d=json.loads(row[1]); content=d.get("content",d.get("text","")); title=d.get("title",row[0])
                if filters.get("kind")=="rule" and not row[0].startswith(("OM-","SOP-")): continue
                if filters.get("asset_id") and d.get("asset_id")!=filters["asset_id"]: continue
                if terms and not all(t in content.lower() for t in terms): continue
                matches.append({"id":row[0],"kind":"document" if row[3]=="document" else "report" if row[3]=="report" else "note","title":title,"source_path":row[2],"excerpt":content[:1000],"content":content})
            return {"matches":matches[:100],"complete":len(matches)<=100,"limitations":["Search uses literal term matching; results capped at 100"]}
        finally: con.close()

    def apply_shared_change(self, change, author_id, request_key):
        if not isinstance(change,dict) or not request_key: raise AppError("invalid_request","Change and request key are required")
        con=sqlite3.connect(self.path); con.row_factory=sqlite3.Row
        try:
            ensure_schema(con); con.commit(); con.execute("BEGIN IMMEDIATE")
            old=con.execute("SELECT * FROM changes WHERE request_key=?",(request_key,)).fetchone()
            if old: return {"change_id":old["change_id"],"status":old["status"],"knowledge_revision":int(con.execute("SELECT value FROM metadata WHERE key='knowledge_revision'").fetchone()[0]),"conflicts":[]}
            if not con.execute("SELECT 1 FROM raw_records WHERE kind='user' AND record_id=?",(author_id,)).fetchone(): raise AppError("not_found","Unknown author",404)
            kind=change.get("kind"); scope=change.get("scope"); target=change.get("target_id"); field=change.get("field"); reason=change.get("reason")
            if kind not in {"shared_claim","field_override","rule_override"} or not reason or not target: raise AppError("invalid_request","Change kind, target and reason are required")
            try:
                start=date.fromisoformat(change["valid_from"]) if change.get("valid_from") else None
                end=date.fromisoformat(change["valid_to"]) if change.get("valid_to") else None
            except (TypeError, ValueError) as exc: raise AppError("invalid_request","Validity dates must use YYYY-MM-DD") from exc
            if start and end and end < start: raise AppError("invalid_request","valid_to cannot precede valid_from")
            if kind=="shared_claim":
                if scope!="well" or not con.execute("SELECT 1 FROM raw_records WHERE kind='asset' AND record_id=?",(target,)).fetchone() or not isinstance(change.get("text"),str): raise AppError("invalid_request","A shared claim requires a well target and text")
                field="claim"; value=None
            elif kind=="field_override":
                if scope!="inspection" or field not in MEASUREMENTS or not con.execute("SELECT 1 FROM raw_records WHERE kind='inspection' AND record_id=?",(target,)).fetchone(): raise AppError("invalid_request","Field corrections require a known inspection and supported measurement")
                value=change.get("value")
                if field in {"wellhead_temp_c","ambient_temp_c","spill_est_volume_bbl"} and (not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value)): raise AppError("invalid_request","Measurement correction must be finite and numeric")
                if field=="spill_est_volume_bbl" and value<0: raise AppError("invalid_request","Spill volume cannot be negative")
                if field=="spill_detected" and not isinstance(value,bool): raise AppError("invalid_request","Spill correction must be boolean")
            else:
                proposed=change.get("value")
                if scope not in {"well","well_type"} or field is None or not isinstance(proposed,(int,float)) or isinstance(proposed,bool) or not math.isfinite(proposed): raise AppError("invalid_request","Rule override requires a supported target and finite numeric value")
                if scope=="well" and not con.execute("SELECT 1 FROM raw_records WHERE kind='asset' AND record_id=?",(target,)).fetchone(): raise AppError("invalid_request","Unknown well target")
                if scope=="well_type" and not con.execute("SELECT 1 FROM assets WHERE well_type=? LIMIT 1",(target,)).fetchone(): raise AppError("invalid_request","Unknown well type")
                well_type = target if scope == "well_type" else con.execute("SELECT json_extract(payload,'$.well_type') FROM raw_records WHERE kind='asset' AND record_id=?",(target,)).fetchone()[0]
                baseline=con.execute("SELECT payload FROM baseline_rules WHERE well_type IN (?, '*') AND rule_key=? LIMIT 1",(well_type,field)).fetchone()
                if not baseline: raise AppError("invalid_request","Unknown rule key")
                if field=="rca_count":
                    if int(proposed)!=proposed or proposed<0: raise AppError("invalid_request","rca_count must be a nonnegative integer")
                    if not change.get("equipment_kind"): raise AppError("invalid_request","rca_count requires equipment_kind")
                    exists=con.execute("SELECT 1 FROM equipment e JOIN assets a USING(asset_id) WHERE a.well_type=? AND e.equipment_kind=? LIMIT 1",(well_type,change["equipment_kind"])) .fetchone()
                    if not exists: raise AppError("invalid_request","Unknown equipment kind for target")
                unit=json.loads(baseline[0]).get("unit")
                value={"rule_key":field,"value":proposed,"unit":unit}
            candidates=con.execute("SELECT * FROM changes WHERE kind=? AND scope=? AND target_id=? AND field=? AND COALESCE(equipment_kind,'')=COALESCE(?,'') AND status='accepted' AND COALESCE(valid_to,'9999-12-31')>=COALESCE(?,'0001-01-01') AND COALESCE(?,'9999-12-31')>=COALESCE(valid_from,'0001-01-01') ORDER BY created_at DESC",(kind,scope,target,field,change.get("equipment_kind"),change.get("valid_from"),change.get("valid_to"))).fetchall() if kind!="shared_claim" else []
            supersedes=change.get("supersedes_id")
            if supersedes and not any(c["change_id"]==supersedes for c in candidates): raise AppError("invalid_request","supersedes_id must name an overlapping accepted correction")
            conflicts=[{"existing_change_id":c["change_id"],"proposed_value":value,"accepted_value":json.loads(c["value_json"] or "null")} for c in candidates if json.loads(c["value_json"] or "null")!=value and c["change_id"]!=supersedes]
            if supersedes:
                if len(conflicts): raise AppError("invalid_request","supersedes_id does not resolve all overlapping conflicts")
                con.execute("UPDATE changes SET status='superseded' WHERE change_id=?",(supersedes,))
            status="pending_conflict" if conflicts else "accepted"
            change_id=f"CHG-{request_key}"
            con.execute("INSERT INTO changes(change_id,request_key,author_id,kind,scope,target_id,field,value_json,reason,equipment_kind,valid_from,valid_to,text,supersedes_id,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(change_id,request_key,author_id,kind,scope,target,field,json.dumps(value) if value is not None else None,reason,change.get("equipment_kind"),change.get("valid_from"),change.get("valid_to"),change.get("text"),change.get("supersedes_id"),status))
            if status=="accepted": con.execute("UPDATE metadata SET value=CAST(value AS INTEGER)+1 WHERE key='knowledge_revision'")
            rev=int(con.execute("SELECT value FROM metadata WHERE key='knowledge_revision'").fetchone()[0]); con.commit()
            return {"change_id":change_id,"status":status,"knowledge_revision":rev,"conflicts":conflicts}
        except Exception:
            if con.in_transaction: con.rollback()
            raise
        finally: con.close()
