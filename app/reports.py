"""Extract explicit report facts and compliance check rows without guessing."""
import re


def extract_report(report_id, asset_id, source_path, text):
    checks = []
    in_checks = False
    for line in text.splitlines():
        if line.strip().lower().startswith("## compliance check"):
            in_checks = True
            continue
        if in_checks and line.startswith("## "):
            break
        if in_checks and line.strip().startswith("|") and not re.search(r"---", line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 3 and cells[0].strip("* ").lower() not in {"protocol", "rule", "requirement"}:
                rule_id = cells[0].strip("* ")
                checks.append({"check_id": f"{report_id}#{rule_id}", "report_id": report_id, "asset_id": asset_id, "rule_id": rule_id, "reported_result": cells[1].strip("* "), "detail": cells[2]})
    facts = []
    patterns = [("containment_hours", r"contained (?:about|after) ([\d.]+) hours?"), ("hours_to_report", r"filed ([\d.]+) hours? after detection"), ("soil_tph_pct", r"(?:highest result after clean-up was|cleaned to) ([\d.]+)% TPH"), ("soil_samples", r"(\d+) soil samples? taken"), ("spill_volume_bbl", r"estimated ([\d.]+) bbl")]
    for key, pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            value = float(match.group(1))
            facts.append({"fact_id": f"{report_id}#{key}", "report_id": report_id, "asset_id": asset_id, "fact_key": key, "value": value, "unit": "hours" if key.endswith("hours") else "% TPH" if key.endswith("pct") else "samples" if key == "soil_samples" else "barrels", "source_text": match.group(0), "read_status": "read"})
    return facts, checks
