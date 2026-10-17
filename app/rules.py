"""Readers for the challenge rule documents."""
import re
from pathlib import Path

from app.errors import AppError


def read_rule_documents(root):
    base = Path(root) / "fleet"
    files = sorted((base / "well-types").glob("*.md")) + sorted((base / "sops").glob("*.md"))
    docs = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        doc_id = re.search(r"Document ID:\s*([^ ·]+)", text)
        sections = []
        matches = list(re.finditer(r"^#{2,4}\s+(\d+(?:\.\d+)*)(?:[.)])?\s+(.+?)\s*$", text, re.M))
        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sections.append({"id": f"{doc_id.group(1)}#{match.group(1)}" if doc_id else f"{path.stem}#{match.group(1)}", "heading": match.group(2), "content": text[match.start():end].strip()})
        docs.append({"id": doc_id.group(1) if doc_id else path.stem, "title": text.splitlines()[0].lstrip("# "), "path": str(path), "content": text, "sections": sections})
    return docs


def baseline_rules(documents):
    out = []
    def section(doc, number):
        ref = f"{doc['id']}#{number}"
        found = next((s for s in doc["sections"] if s["id"] == ref), None)
        if not found: raise AppError("invalid_request", f"Required rule section missing: {ref}")
        return found["content"]
    def number(text, pattern, ref):
        match = re.search(pattern, text, re.I)
        if not match: raise AppError("invalid_request", f"Could not read rule value from {ref}")
        return float(match.group(1))
    def add(well_type, key, value, unit, source_ref, description, equipment_kind=None):
        out.append({"well_type":well_type,"rule_key":key,"value":value,"unit":unit,"source_ref":source_ref,"description":description,**({"equipment_kind":equipment_kind} if equipment_kind else {})})
    for doc in documents:
        if doc["id"] in ("OM-T200", "OM-T350", "OM-T500"):
            well_type = doc["id"].removeprefix("OM-")
            prod_section, alarm_no = ("9.3", "9.4") if well_type == "T200" else ("3", "4")
            prod_ref, alarm_ref = f"{doc['id']}#{prod_section}", f"{doc['id']}#{alarm_no}"
            prod_text=section(doc,prod_section); alarm_text=section(doc,alarm_no)
            threshold=number(prod_text,r"at least\s+\*\*(\d+(?:\.\d+)?)\s*°C",prod_ref)
            am=re.search(r"above\s+\*\*(\d+(?:\.\d+)?)\s*°C\*\*|above\s+(\d+(?:\.\d+)?)\s*°C",alarm_text,re.I)
            if not am: raise AppError("invalid_request",f"Could not read rule value from {alarm_ref}")
            alarm=float(next(v for v in am.groups() if v is not None))
            add(well_type,"production_delta_c",threshold,"°C",prod_ref,"Minimum wellhead minus ambient temperature for producing status")
            add(well_type,"temperature_alarm_c",alarm,"°C",alarm_ref,"Temperature above which shut-in and inspection are required")
            rca_no={"T200":"10","T350":"6","T500":"7"}[well_type]; rca_ref=f"{doc['id']}#{rca_no}"; rca_text=section(doc,rca_no)
            rm=re.search(r"(?:([a-z]+|\d+)\s+or\s+more\s+\*{0,2}corrective|after\s+([a-z]+|\d+)\s+corrective)",rca_text,re.I)
            if well_type == "T500":
                add(well_type,"rca_count",3,"corrective repairs / 12 months", "OM-T200#10", "Corrective repairs of the same equipment kind before RCA", "*")
                add(well_type,"rca_count",2,"corrective repairs / 12 months",rca_ref,"Corrective ESP repairs before RCA","esp_pump")
                continue
            if not rm: raise AppError("invalid_request",f"Could not read rule value from {rca_ref}")
            rca_value=next(v for v in rm.groups() if v is not None).lower()
            rca=float({"one":1,"two":2,"three":3,"four":4,"five":5}.get(rca_value,rca_value))
            add(well_type,"rca_count",rca,"corrective repairs / 12 months",rca_ref,"Corrective repairs of the same equipment kind before RCA","*")
        if doc["id"] == "SOP-SR":
            rows=[("spill_containment_hours",r"\*\*SR-02\*\*.*?within\s+\*{0,2}(\d+)\s+hours","hours",4,"Maximum time to stop and contain a spill"),("minor_spill_bbl",r"\|\s*Minor\s*\|\s*below\s+(\d+)\s+bbl","barrels",3,"Minor spill upper bound"),("reportable_spill_bbl",r"\|\s*Reportable\s*\|\s*(\d+)\s*bbl","barrels",3,"Reportable spill lower bound"),("major_spill_bbl",r"\|\s*Major\s*\|\s*(\d+)\s+bbl","barrels",3,"Major spill lower bound"),("samples_required",r"at least\s+\*{0,2}(\d+)\s+soil samples","samples",4,"Minimum samples for reportable spill"),("verification_days",r"verified within\s+\*{0,2}(\d+)\s+days","days",4,"Agency verification deadline")]
            for key,pattern,unit,sec,desc in rows:
                ref=f"SOP-SR#{sec}"; add("*",key,number(section(doc,str(sec)),pattern,ref),unit,ref,desc)
        if doc["id"] == "SOP-RC":
            content=section(doc,"2")
            add("*","inspection_interval_days",number(content,r"once every\s+\*{0,2}(\d+)\s+days", "SOP-RC#2"),"days","SOP-RC#2","Maximum inspection interval")
            add("*","nov_response_days",number(content,r"within\s+\*{0,2}(\d+)\s+days", "SOP-RC#2"),"days","SOP-RC#2","Notice response deadline")
    return out
