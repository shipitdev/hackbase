#!/usr/bin/env python3
"""Build the two-page local evaluation writeup (Chrome PDF + editable DOCX)."""
from pathlib import Path
import base64, html, shutil, subprocess, tempfile, zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'submission'
TMP = ROOT / 'data/writeup'
SVG = ROOT / 'docs/diagrams/video-system.svg'
PNG = TMP / 'architecture.png'
HTML = TMP / 'writeup.html'
PDF = OUT / 'asset-intelligence-writeup.pdf'
DOCX = OUT / 'asset-intelligence-writeup.docx'
TMP.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

# QuickLook square canvases wide SVGs; render through a square viewBox, then crop
# exactly the original 1600x900 diagram viewport for a complete Word fallback.
from PIL import Image
import re
svg_text = SVG.read_text(encoding='utf-8')
square_text = re.sub(r'<svg\b[^>]*>', '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1600" viewBox="0 0 1600 1600">', svg_text, count=1)
square_svg = TMP / 'architecture-square.svg'
square_svg.write_text(square_text, encoding='utf-8')
subprocess.run(['qlmanage','-t','-s','1600','-o',str(TMP),str(square_svg)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
im = Image.open(TMP / 'architecture-square.svg.png').convert('RGB')
if im.size != (1600,1600):
    raise RuntimeError(f'Unexpected square preview size: {im.size}')
im.crop((0,0,1600,900)).save(PNG)

rows = [
('Q1 · Pressure','Supported refusal: pressure is unmeasured; no map.','Scanned 125,198 inspections; zero pressure matches; cited equipment inventory.'),
('Q2 · Producer','HTTP 502 upstream error; no answer.','Source has no per-well oil-volume measure; refusal to rank barrels is warranted.'),
('Q3 · Gas reports','HTTP 502; no table.','No answer to assess. Reference oracle only: 26 reports; 17 met deadline, 9 missed.'),
('Q4 · Bypasses','Context-limit partial; no table, citations or results.','No answer to assess. Reference oracle only: 12 intervals, 3 current, 5 violations.'),
('Q5 · Regulator','Context-limit partial; no table or evidence.','Not verifiable.'),
('Q6 · Disagreement','Context-limit partial; no table or evidence.','Not verifiable.'),
('Q7 · Repair risk','Both turns context-limit partial; no ranking.','No crew recommendation or table; no unique oracle ranking.'),
('Q8 · Recall','Turns 1–2: HTTP 502; turns 3–5: context-limit partial.','No recall tables or sourced facts; no shared change saved, persistence not demonstrated.'),
('Q9 · Multi-topic','Turn 2: Nathan Pierce, 150 TEAM-NW wells. T1/T5 partial; T3/T4/T6 HTTP 502.','Turn 2 supported by four saved-query citations. T4 got no answer; no Dec 3 H2S reading, latest documented earlier value 0 ppm on Nov 20.'),
('Q10 · Workload','HTTP 502; no table or stacked bar.','Not verifiable.'),
('Q11 · Region','HTTP 502; no evidence or comparison.','Not verifiable.'),
]
trs=''.join('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in row)+'</tr>' for row in rows)
svg_data='data:image/svg+xml;base64,'+base64.b64encode(SVG.read_bytes()).decode()
css='''
@page { size: A4 landscape; margin: 8mm 9mm 8mm; }
* { box-sizing:border-box }
body { font-family: Arial, Helvetica, sans-serif; color:#152238; margin:0; font-size:9pt; line-height:1.22 }
.page { width:100%; height:194mm; position:relative; overflow:hidden; page-break-after:always }
.page:last-child { page-break-after:auto }
h1 { font-size:20pt; margin:0 0 1mm; letter-spacing:-.3pt }
.kicker { color:#42607d; font-size:8pt; text-transform:uppercase; letter-spacing:1.1pt; margin-bottom:1mm }
.sub { font-size:9pt; color:#52657a; margin:0 0 2mm }
.diagram { display:block; width:100%; height:137mm; object-fit:contain; border:1px solid #dce4ec }
.caption { color:#52657a; font-size:7.3pt; margin:1mm 0 2mm }
.facts { display:grid; grid-template-columns: 1fr 1fr 1fr; gap:3mm; font-size:8pt }
.facts div { border-top:1px solid #cad5e0; padding-top:1mm }
strong { color:#102d48 }
a { color:#1769aa; text-decoration:none }
h2 { font-size:16pt; margin:0 0 1mm }
.intro { margin:0 0 2mm; color:#52657a; font-size:8pt }
table { width:100%; border-collapse:collapse; table-layout:fixed; font-size:9pt; line-height:1.16 }
th { text-align:left; background:#173c5b; color:white; padding:1.7mm 1.4mm; font-size:9pt }
td { vertical-align:top; padding:1.7mm 1.4mm; border-bottom:1px solid #d7e0e8 }
tr:nth-child(even) td { background:#f3f7fa }
th:nth-child(1),td:nth-child(1){width:18%} th:nth-child(2),td:nth-child(2){width:36%} th:nth-child(3),td:nth-child(3){width:46%}
.notes { margin-top:2mm; display:grid; grid-template-columns:1fr 1fr; gap:3mm; font-size:8.4pt; line-height:1.2 }
.note { border-left:2px solid #4a9eed; padding-left:2mm }
.footer { position:absolute; bottom:0; left:0; right:0; border-top:1px solid #d7e0e8; padding-top:1mm; font-size:6.8pt; color:#617286; display:flex; justify-content:space-between }
'''
body=f'''<section class="page"><div class="kicker">System design · final release</div><h1>Asset Intelligence Copilot</h1><p class="sub">A source-grounded assistant for 600 wells across seven areas · calculation date: 15 January 2027</p><img class="diagram" src="{svg_data}"/><p class="caption">Runtime uses one copilot with five bounded tools; the Sol/Luna labels describe build-time roles, not runtime agents.</p><div class="facts"><div><strong>Data path</strong><br>Loader places the released dataset in a shared SQLite database. Private chats live separately in a second SQLite database.</div><div><strong>Answer path</strong><br>SQL queries, evidence lookup, FTS5 manual/SOP search, recall and remember support answers. Saved query rows feed validated OpenUI components.</div><div><strong>Safeguards</strong><br>Original records remain intact; accepted scoped corrections inform later calculations. Private memory access is owner-checked. Demo user selection is not production authentication.</div></div><div class="footer"><span>Public source: <a href="https://github.com/shipitdev/hackbase">github.com/shipitdev/hackbase</a></span><span>DO inference router · budget preference enabled · no measured cost claim</span></div></section>
<section class="page"><div class="kicker">Evaluation · 11 released questions</div><h2>Evaluation results and limits</h2><p class="intro"><strong>Updated pipeline run in progress:</strong> 16/21 turns attempted as of 17 Oct 2026: 11 HTTP 200 partials, 4 HTTP 502 errors, 1 request pending. Partial HTTP success does not establish correctness; these new answers have not yet completed evidence review. The table below reports the separate, completed E4 run.</p><table><thead><tr><th>Question</th><th>Earlier full run (E4)</th><th>Evidence review</th></tr></thead><tbody>{trs}</tbody></table><div class="notes"><div class="note"><strong>E4 result:</strong> Q1 refusal and Q9-2 (Nathan Pierce, 150 wells) were the only supported answers: 2/21 verified answer coverage, not an accuracy rate. Q9-2 had four saved-query citations. Q9-4 had no answer; source records contain no Dec 3 H2S reading. Oracle counts above are reference checks, not model outputs.</div><div class="note"><strong>Limits:</strong> E4’s other 19 turns were unverifiable. It recorded at least 1,740,380 tokens; no cost total is stated. Full runtime conversations remain private. <a href="https://github.com/shipitdev/hackbase/blob/main/tasks/reports/E4-final-rerun.md">E4 report</a> · <a href="https://github.com/shipitdev/hackbase/blob/main/tasks/reports/E4-source-oracles.md">source checks</a>. Dataset: 125,198 inspections and 17,415 maintenance records.</div></div><div class="footer"><span>Private captures and databases are excluded.</span><span>E4: 21 turns · no complete scenario</span></div></section>'''
HTML.write_text('<!doctype html><html><head><meta charset="utf-8"><style>'+css+'</style></head><body>'+body+'</body></html>',encoding='utf-8')
chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
profile=TMP/'chrome-profile'
subprocess.run([chrome,'--headless=new','--disable-gpu',f'--user-data-dir={profile}','--no-pdf-header-footer',f'--print-to-pdf={PDF}',HTML.as_uri()],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
# Editable DOCX: convert text/table with textutil, then insert source diagram and explicit page break.
doc_html=HTML.read_text().replace(f'<img class="diagram" src="{svg_data}"/>','<p>ARCHITECTUREIMAGE</p>')
# data URI is intentionally absent from Word source; hyperlink targets stay text-visible.
wordhtml=TMP/'writeup-word.html'; wordhtml.write_text(doc_html,encoding='utf-8')
subprocess.run(['textutil','-convert','docx',str(wordhtml),'-output',str(DOCX)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'; R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'; A='http://schemas.openxmlformats.org/drawingml/2006/main'; WP='http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'; PIC='http://schemas.openxmlformats.org/drawingml/2006/picture'
ET.register_namespace('w',W); ET.register_namespace('r',R); ET.register_namespace('a',A); ET.register_namespace('wp',WP); ET.register_namespace('pic',PIC)
with zipfile.ZipFile(DOCX) as z: files={n:z.read(n) for n in z.namelist()}
doc=ET.fromstring(files['word/document.xml'])
# Replace placeholder paragraph's run with inline image drawing.
for p in doc.iter('{%s}p'%W):
    if 'ARCHITECTUREIMAGE' in ''.join(t.text or '' for t in p.iter('{%s}t'%W)):
        for ch in list(p): p.remove(ch)
        run=ET.SubElement(p,'{%s}r'%W); drawing=ET.SubElement(run,'{%s}drawing'%W); inline=ET.SubElement(drawing,'{%s}inline'%WP)
        ET.SubElement(inline,'{%s}extent'%WP,{'cx':'9144000','cy':'5143500'})
        ET.SubElement(inline,'{%s}docPr'%WP,{'id':'1','name':'System design diagram'})
        nvf=ET.SubElement(inline,'{%s}cNvGraphicFramePr'%WP); ET.SubElement(nvf,'{%s}graphicFrameLocks'%A,{'noChangeAspect':'1'})
        graphic=ET.SubElement(inline,'{%s}graphic'%A); gd=ET.SubElement(graphic,'{%s}graphicData'%A,{'uri':'http://schemas.openxmlformats.org/drawingml/2006/picture'})
        pic=ET.SubElement(gd,'{%s}pic'%PIC); nv=ET.SubElement(pic,'{%s}nvPicPr'%PIC); ET.SubElement(nv,'{%s}cNvPr'%PIC,{'id':'0','name':'architecture.png'}); ET.SubElement(nv,'{%s}cNvPicPr'%PIC)
        fill=ET.SubElement(pic,'{%s}blipFill'%PIC); ET.SubElement(fill,'{%s}blip'%A,{'{%s}embed'%R:'rId3'}); st=ET.SubElement(fill,'{%s}stretch'%A); ET.SubElement(st,'{%s}fillRect'%A)
        sp=ET.SubElement(pic,'{%s}spPr'%PIC); xf=ET.SubElement(sp,'{%s}xfrm'%A); ET.SubElement(xf,'{%s}off'%A,{'x':'0','y':'0'}); ET.SubElement(xf,'{%s}ext'%A,{'cx':'9144000','cy':'5143500'}); geom=ET.SubElement(sp,'{%s}prstGeom'%A,{'prst':'rect'}); ET.SubElement(geom,'{%s}avLst'%A)
    if any((t.text or '').strip()=='Saved answers and results' for t in p.iter('{%s}t'%W)):
        ppr=p.find('{%s}pPr'%W)
        if ppr is None: ppr=ET.Element('{%s}pPr'%W); p.insert(0,ppr)
        ET.SubElement(ppr,'{%s}pageBreakBefore'%W)
# Set the editable document to landscape A4 with compact margins.
for sect in doc.iter('{%s}sectPr'%W):
    pg=sect.find('{%s}pgSz'%W)
    if pg is None: pg=ET.SubElement(sect,'{%s}pgSz'%W)
    pg.set('{%s}w'%W,'16838'); pg.set('{%s}h'%W,'11906'); pg.set('{%s}orient'%W,'landscape')
    mar=sect.find('{%s}pgMar'%W)
    if mar is None: mar=ET.SubElement(sect,'{%s}pgMar'%W)
    for k in ('top','right','bottom','left'): mar.set('{%s}%s'%(W,k),'510')
files['word/document.xml']=ET.tostring(doc,encoding='utf-8',xml_declaration=True)
rels=ET.fromstring(files['word/_rels/document.xml.rels']); nsrel='{http://schemas.openxmlformats.org/package/2006/relationships}'
ET.SubElement(rels,nsrel+'Relationship',{'Id':'rId3','Type':'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image','Target':'media/architecture.png'})
files['word/_rels/document.xml.rels']=ET.tostring(rels,encoding='utf-8',xml_declaration=True)
ct=ET.fromstring(files['[Content_Types].xml']); ET.SubElement(ct,'{http://schemas.openxmlformats.org/package/2006/content-types}Default',{'Extension':'png','ContentType':'image/png'}); files['[Content_Types].xml']=ET.tostring(ct,encoding='utf-8',xml_declaration=True)
files['word/media/architecture.png']=PNG.read_bytes()
with zipfile.ZipFile(DOCX,'w',zipfile.ZIP_DEFLATED) as z:
    for n,b in files.items(): z.writestr(n,b)
print(f'Wrote {PDF} and {DOCX}')
