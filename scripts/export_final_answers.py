"""Export completed official evaluation answers without private databases or traces."""
import html
import json
import sys
import zipfile
from pathlib import Path


def escaped(value):
    return html.escape(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False))


def export(source, target):
    state = json.loads((source / 'state.json').read_text())
    steps = state.get('steps', {})
    if len(steps) != 21 or any(v.get('status') == 'attempt_pending' for v in steps.values()):
        raise ValueError('The ordered 21-turn run must finish before export.')
    records = []
    for question in range(1, 12):
        folder = source / f'Q{question}'
        for path in sorted(folder.glob('*.json')):
            record = json.loads(path.read_text())
            if record.get('name') in steps:
                records.append((path, record))
    if len(records) != 21:
        raise ValueError('Expected exactly 21 saved turn records.')
    sections = []
    for path, record in records:
        answer = record.get('response', {})
        parts = [f'<section><h2>{escaped(record["name"])}</h2>',
                 f'<p><strong>Question</strong> {escaped(record.get("text", ""))}</p>',
                 f'<p>HTTP {escaped(record.get("status_code", "not captured"))}; status {escaped(answer.get("status", "error"))}</p>',
                 f'<div class="answer">{escaped(answer.get("answer", record.get("error", "No answer returned.")))}</div>']
        for result in answer.get('results', {}).values():
            columns = [c['name'] for c in result.get('columns', [])]
            header = ''.join(f'<th>{escaped(c)}</th>' for c in columns)
            rows = ''.join('<tr>' + ''.join(f'<td>{escaped(row.get(c))}</td>' for c in columns) + '</tr>' for row in result.get('rows', []))
            parts.append(f'<div class="scroll"><table><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table></div>')
        for title, value in [('Visual specification', answer.get('ui')), ('Citations', answer.get('citations')), ('Limitations', answer.get('limitations')), ('Conflicts', answer.get('conflicts')), ('Error', answer.get('error'))]:
            if value:
                parts.append(f'<details><summary>{title}</summary><pre>{escaped(json.dumps(value, ensure_ascii=False, indent=2))}</pre></details>')
        sections.append(''.join(parts) + '</section>')
    page = '<!doctype html><meta charset="utf-8"><title>Final evaluation answers</title><style>body{font:16px system-ui;max-width:1100px;margin:32px auto;padding:0 20px;color:#172536}section{border-top:1px solid #bbb;padding:20px 0}.answer,pre{white-space:pre-wrap;overflow-wrap:anywhere}.scroll{overflow:auto}table{border-collapse:collapse;font-size:14px}th,td{padding:7px;border:1px solid #ccc;text-align:left}summary{cursor:pointer;margin-top:12px}</style><h1>Final evaluation answers</h1><p>All 21 official evaluation turns in order. These are captured outputs, not an accuracy claim. Visual specifications and their saved rows are preserved; this export does not execute generated UI. Private databases and tool traces are excluded.</p>' + ''.join(sections)
    target.mkdir(parents=True, exist_ok=True)
    (target / 'final-answers.html').write_text(page)
    bundle = target / 'final-evaluation-answers.zip'
    with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('final-answers.html', page)
        for path, record in records:
            archive.writestr(f'answers/{record["name"]}.json', json.dumps(record, ensure_ascii=False, indent=2))
    return bundle


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == '--self-check':
        assert escaped('<script>') == '&lt;script&gt;'
        assert '&quot;' in escaped({'label': 'quoted'})
        print('HTML escaping self-check passed')
    elif len(sys.argv) == 3:
        print(export(Path(sys.argv[1]), Path(sys.argv[2])))
    else:
        raise SystemExit('Usage: export_final_answers.py INPUT_RUN OUTPUT_DIR | --self-check')
