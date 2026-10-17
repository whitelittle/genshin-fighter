from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'outputs/three-role-redesign-20261014';B=R/'outputs/three-role-basic-20261013'
cards=json.loads((O/'all-design-cards.json').read_text(encoding='utf8'));assert len(cards)==75
assert len({(c['role'],c['actionId']) for c in cards})==75
assert all(c['continuation'] and len(c['phases'])>=4 and not c['artAccepted'] for c in cards)
checks=json.loads((O/'browser-checks.json').read_text(encoding='utf8'));assert len(checks)==64
expected={'zhongli':{'standguard','light1'},'mavuika':{'heavy'},'neuvillette':{'E'}}
assert all(c['selected'] in expected[c['role']] and c['ready'] for c in checks)
coverage=json.loads((O/'coverage-browser-checks.json').read_text(encoding='utf8'));assert sorted((c['all'],c['missing']) for c in coverage)==[(25,0),(25,12),(25,18)]
objects=[];refs=0
for role in expected:
 D=O/role;bank=json.loads((D/'actions.json').read_text(encoding='utf8'))
 for key,g in bank.items():
  assert len(g['frames'])==len(g['sourceFrames'])==len(g['durations'])==len(g['phases'])
  for mode in ['sourceFrames','frames']:
   for f in g[mode]:assert (D/f['file']).exists();refs+=1
 for p in (D/'fit').glob('*.json'):
  m=json.loads(p.read_text());im=np.array(Image.open(D/m['file']).convert('RGBA'));rebuild=np.zeros_like(im)
  for x,y,w,h,c in m['rects']:rebuild[y:y+h,x:x+w]=m['palette'][c]+[255]
  assert np.array_equal(im,rebuild);objects.append({'role':role,'file':p.relative_to(O).as_posix(),'rectangles':len(m['rects']),'exact':True})
assert len(objects)==16
old=json.loads((B/'delivery-strict-review-20261014.json').read_text(encoding='utf8'))
unchanged={}
for role in expected:
 path=f'outputs/three-role-basic-20261013/{role}/actions.json';sha=next(f['sha256'] for f in old['files'] if f['path']==path);unchanged[role]=hashlib.sha256((R/path).read_bytes()).hexdigest()==sha
assert all(unchanged.values())
report={'designCards':75,'coverageUI':coverage,'bodyObjects':objects,'bodyFrameReferences':refs,'browserPhaseChecks':64,'oldMasterActionTablesUnchanged':unchanged,'artAccepted':False,'runtimeIntegrated':False,'deviceVerified':False}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
note='> 2026-10-14 最新三角色决定：用户指出火神/水龙缺大量动作，要求钟离重新设计。已补全三人75张逐动作设计卡，火神主预览仍缺18组、水龙12组；钟离全25组按直立、短步、定式发力、从容收势重设计。新增钟离站防/轻1、火神站重、水龙E共4组身体方向小样，16对象精确重建、64浏览器阶段检查及设计表筛选通过；旧主动作表保留，完整制作/美术/正式战斗/真机仍未完成。先读[完整补缺与钟离重设计](docs/current/三角色完整动作补缺与钟离重设计_20261014.md)，新工作台`outputs/three-role-redesign-20261014/index.html`。本决定优先于此前仅修钟离蹲伏的安排。\n\n'
f=R/'AI_START.md';s=f.read_text(encoding='utf8')
if not s.startswith('> 2026-10-14 最新三角色决定：'):f.write_text(note+s,encoding='utf8')
f=R/'docs/current/V9_执行与验收台账_20261013.md';s=f.read_text(encoding='utf8');note=note.replace('docs/current/三角色完整动作补缺与钟离重设计_20261014.md','三角色完整动作补缺与钟离重设计_20261014.md')
if not s.startswith('> 2026-10-14 最新三角色决定：'):f.write_text(note+s,encoding='utf8')
f=B/'index.html';s=f.read_text(encoding='utf8');link='<a href="../three-role-redesign-20261014/index.html" target="_blank">最新完整补缺与钟离重设计</a>'
if link not in s:s=s.replace('<a href="本批记录.md"',link+'<a href="本批记录.md"');f.write_text(s,encoding='utf8')
manifest={'date':'2026-10-14','scope':'75 visual design cards and 4 incomplete body samples','artAccepted':False,'runtimeIntegrated':False,'deviceVerified':False,'files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(O.rglob('*')) if p.is_file() and p.name!='delivery.json']}
(O/'delivery.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'cards':75,'objects':16,'bodyRefs':refs,'browserChecks':64,'oldMasterUnchanged':unchanged},ensure_ascii=False))
