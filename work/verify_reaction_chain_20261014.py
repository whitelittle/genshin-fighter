from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'outputs/three-role-redesign-20261014';B=R/'outputs/three-role-basic-20261013'
rectChecks=[];refs=0
for role in ['mavuika','neuvillette']:
 for directory in [O/role,B/role]:
  bank=json.loads((directory/'actions.json').read_text(encoding='utf8'))
  assert bank['hit_knockdown']['frames'][-1]==bank['wakeup']['frames'][0]
  assert bank['hit_knockdown']['sourceFrames'][-1]==bank['wakeup']['sourceFrames'][0]
  assert bank['wakeup']['frames'][-1]==bank['idle']['frames'][0]
  for key in ['hit_knockdown','wakeup']:
   g=bank[key];assert len(g['frames'])==len(g['sourceFrames'])==len(g['durations'])==len(g['phases'])==6
   for mode in ['frames','sourceFrames']:
    for f in g[mode]:assert (directory/f['file']).resolve().exists();refs+=1
 for file in (O/role/'fit').glob('*chain-20261014-*.json'):
  d=json.loads(file.read_text(encoding='utf8'));target=np.array(Image.open(O/role/d['file']).convert('RGBA'));actual=np.zeros_like(target)
  for x,y,w,h,c in d['rects']:actual[y:y+h,x:x+w]=d['palette'][c]+[255]
  assert np.array_equal(actual,target);rectChecks.append(file.relative_to(O).as_posix())
assert len(rectChecks)==20
browser=json.loads((O/'reaction-browser-checks-20261014.json').read_text(encoding='utf8'));assert len(browser)==96
assert all(c['ready'] and c['selected'] in ['hit_knockdown','wakeup'] for c in browser)
boundaries=json.loads((O/'reaction-boundary-browser-20261014.json').read_text());assert len(boundaries)==2 and all(c['sameFile'] and c['sameRoot'] for c in boundaries)
play=json.loads((O/'reaction-chain-playback-20261014.json').read_text());assert play['mavuikaEndedAtIdle'] and play['neuvilletteEnd']['selected']=='idle'
coverage=json.loads((O/'coverage.json').read_text(encoding='utf8'));assert len(coverage['roles']['mavuika']['missingMainPreview'])==16;assert len(coverage['roles']['neuvillette']['missingMainPreview'])==10
report={'scope':'independent body previews, not combat simulation','newGroups':4,'newBodies':20,'newMainPreviewStates':24,'exactReconstructionObjects':rectChecks,'newBodyReferences':refs,'browserPhaseStartChecks':96,'sharedDownBoundaries':boundaries,'chainReplayEndsAtIdle':True,'designDirectionAcceptedByUser':True,'artAccepted':False,'runtimeIntegrated':False,'deviceVerified':False}
(O/'reaction-verification-20261014.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
note='> 2026-10-14 最新受击起身接续：用户认可新设计并要求继续。火神/水龙受击倒地与起身4组20新身体图已进入新稿页和原主预览；倒地边界共用图/锚点，连播回母版。20对象重建、96浏览器阶段及双角色边界/连播通过；主预览火神9组46状态、水龙15组79状态，仍缺16/10组。“全套”仅文字设计的误导已纠正，播放器仅列可播放动作。设计方向认可，人体/武器/全部美术/正式战斗/真机未验。详见[当前接续](docs/current/三角色完整动作补缺与钟离重设计_20261014.md)顶部，新稿入口`outputs/three-role-redesign-20261014/index.html`。\n\n'
f=R/'AI_START.md';s=f.read_text(encoding='utf8')
if not s.startswith('> 2026-10-14 最新受击起身接续：'):f.write_text(note+s,encoding='utf8')
f=R/'docs/current/V9_执行与验收台账_20261013.md';s=f.read_text(encoding='utf8')
if not s.startswith('> 2026-10-14 最新受击起身接续：'):f.write_text(note.replace('docs/current/三角色完整动作补缺与钟离重设计_20261014.md','三角色完整动作补缺与钟离重设计_20261014.md')+s,encoding='utf8')
manifest={'date':'2026-10-14','scope':'8 body preview groups plus 75 visual design cards; animation production remains incomplete','designDirectionAcceptedByUser':True,'artAccepted':False,'runtimeIntegrated':False,'deviceVerified':False,'files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ['delivery.json','delivery-reaction-20261014.json']]}
(O/'delivery-reaction-20261014.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'newBodies':20,'refs':refs,'browserChecks':96,'sharedBoundariesExact':True,'mainMavuika':'9/25','mainNeuvillette':'15/25','artAccepted':False}))
