from pathlib import Path
import json,shutil,re,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import clorinde_assets as ca
R=Path(__file__).resolve().parents[1];B=R/'outputs/three-role-basic-20261013';O=R/'outputs/three-role-redesign-20261014'
plans={('zhongli','standguard'):(.64,[(481,520),(1082,520),(490,1014),(1053,1015)],[8,18,6,12],['直立准备','沉稳抬掌','小幅承压','从容收掌']),('zhongli','light1'):(.64,[(360,520),(1080,520),(365,1008),(1110,1018)],[8,6,3,15],['持枪定式','短转腰预备','直立短刺','原路收枪']),('mavuika','heavy'):(.41,[(470,546),(1190,558),(465,987),(1118,994)],[8,8,4,20],['双手蓄肩','腰髋带剑','前下重斩','制动收剑']),('neuvillette','E'):(.48,[(480,510),(1050,507),(483,1012),(1088,1012)],[8,10,4,24],['扶杖聚势','指示固定落点','下压召瀑','收掌回杖'])}
audits=[];books={}
for role in ['zhongli','mavuika','neuvillette']:
 D=O/role
 for d in ['frames','fit','evidence']:(D/d).mkdir(exist_ok=True)
 old=json.loads((B/role/'actions.json').read_text(encoding='utf8'));idle=next(g for g in old.values() if g.get('actionId')=='zhongli_idle') if role=='zhongli' else old['idle']
 sourceRef=idle['sourceFrames'][0];fitRef=idle['frames'][0]
 shutil.copy2(B/role/sourceRef['file'],D/'frames/reference.png');shutil.copy2(B/role/fitRef['file'],D/'fit/reference.png')
 sf={**sourceRef,'file':'frames/reference.png','source':'frames/reference.png'};ff={**fitRef,'file':'fit/reference.png'}
 bank={'idle':{'sourceFrames':[sf],'frames':[ff],'durations':[60],'phases':['历史母版对照'],'events':[],'status':'仅复用历史母版供人体对照，未制作新待机'}}
 palette=json.loads((B/role/'rects/idle-0-optimized.json').read_text())['palette'] if role=='zhongli' else (json.loads((B/role/'palette.json').read_text()) if role=='neuvillette' else json.loads((B/'upstream/mavuika-v10/dist/assets/neutral-rig-v6.json').read_text())['palette'])
 for (r,key),(unit,roots,durations,phases) in plans.items():
  if r!=role:continue
  ca.O=D;src=D/'sources'/f'{key}.png';items,fragments=ca.extract(src,4);ss=[];fs=[]
  for i,((im,info),root) in enumerate(zip(items,roots)):
   assert not info['fullCanvasContact'],(role,key,i)
   ox,oy=info['sourceOrigin'];anchor=[root[0]-ox+32,root[1]-oy+32];pad=Image.new('RGBA',(im.width+64,im.height+64));pad.alpha_composite(im,(32,32));file=f'frames/{key}-{i}.png';pad.save(D/file)
   source={'file':file,'source':f'sources/{key}.png','scale':unit,'anchor':anchor,'roi':info['roi'],'sourceOrigin':[ox-32,oy-32],'sourceUnitPolicy':'whole-sheet provisional anatomical unit, no per-pose bounding normalization'}
   fitted,meta=ca.canonical_fit(pad,anchor,unit,palette,f'{key}-{i}');ss.append(source);fs.append(fitted)
   audits.append({'role':role,'key':key,'pose':i,'unit':unit,'rootSheet':root,'reconstructionExact':True,'rectangles':fitted['rectangles'],'sourceCanvasContact':False,'artAccepted':False})
  bank[key]={'sourceFrames':ss,'frames':fs,'durations':durations,'phases':phases,'events':[],'status':'2026-10-14新设计身体小样；比例/武器/动作衔接/源板留白仍待美术验收；不代表角色全动作已补齐，未接特效/判定/正式战斗'}
  if role=='zhongli' and key=='light1':bank[key]['status']+='；起止均为持枪态，母版到持枪的装备连接尚未制作，禁止瞬间切枪'
  font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17);card=Image.new('RGBA',(1500,450),(99,111,119,255));dr=ImageDraw.Draw(card)
  for i,f in enumerate([ff]+fs):
   im=Image.open(D/f['file']).convert('RGBA');s=f['scale']*.85;im=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST);card.alpha_composite(im,(round(180+i*300-f['anchor'][0]*s),round(408-f['anchor'][1]*s)));dr.text((i*300+10,12),(['母版对照']+phases)[i],font=font,fill='white')
  dr.line((0,408,1500,408),fill='white');card.convert('RGB').save(D/'evidence'/f'{key}-comparison.png')
 (D/'actions.json').write_text(json.dumps(bank,ensure_ascii=False,indent=2),encoding='utf8');(D/'action-data.js').write_text('window.NEUVILLETTE_ACTIONS='+json.dumps(bank,ensure_ascii=False)+';',encoding='utf8');(D/'effect-data.js').write_text('window.NEUVILLETTE_FX={};',encoding='utf8')
 for name in ['player.css','player.js']:shutil.copy2(B/'mavuika'/name,D/name)
 page=(B/'mavuika/player.html').read_text(encoding='utf8').replace('玛薇卡',{'zhongli':'钟离','mavuika':'玛薇卡','neuvillette':'那维莱特'}[role]);page=re.sub(r'V9累计.*?显示状态候选','新设计身体小样 · 全角色动作仍未完成',page)
 page=page.replace('href="../../../docs/current/三角色动作严格审查与续作_20261014.md"','href="../../../docs/current/三角色完整动作补缺与钟离重设计_20261014.md"').replace('href="current-status.json"','href="../coverage.json"').replace('href="../strict-review-20261014.json"','href="../sample-verification.json"')
 (D/'player.html').write_text(page,encoding='utf8');books[role]=bank
report={'scope':'4 visual body samples only','reconstructionChecks':16,'audit':audits,'artAccepted':False,'runtimeIntegrated':False,'deviceVerified':False}
(O/'sample-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
cards=json.loads((O/'all-design-cards.json').read_text(encoding='utf8'))
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>三角色完整动作设计 · 钟离重设计</title><style>body{background:#111625;color:#eee;font:16px system-ui;margin:0}header,section{padding:22px 28px}h1{font-size:26px}p{line-height:1.7;color:#c4ccda}button,select{font:inherit;color:#eee;background:#2e3a50;border:1px solid #667389;padding:10px;cursor:pointer}button[aria-pressed=true]{background:#665037}a{color:#c5d9ff}iframe{width:100%;height:1000px;border:0}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:12px;border-bottom:1px solid #475064;text-align:left;vertical-align:top}td:nth-child(2){width:42%}.pill{color:#eac17b}.toolbar{display:flex;gap:12px;flex-wrap:wrap}</style><header><h1>完整动作补缺 · 钟离重新设计</h1><p>火神主预览7/25组，水龙13/25组；缺项分别18、12组。这里补全三人75张逐动作设计卡，制作仍未完成。钟离旧25组按“直立、短步、定式发力、从容收势”全部重审；本批只有4组身体小样，不能计为整角色完成。</p><div class="toolbar"><button data-role="zhongli" aria-pressed="true">钟离 · 全套重设计</button><button data-role="mavuika">火神 · 18组待补</button><button data-role="neuvillette">水龙 · 12组待补</button></div><p><a href="../../docs/current/三角色完整动作补缺与钟离重设计_20261014.md">设计与制作顺序</a> · <a href="../role-design-reference-20261014/index.html">历史提示词</a> · <a href="../three-role-basic-20261013/index.html">旧主预览</a></p></header><iframe id="viewer" src="zhongli/player.html" title="新方向身体小样"></iframe><section><h2 id="roleTitle">钟离：25组重新设计</h2><p>新设计卡与现有素材分别登记。技能特效、双人投技、首尾连接、正式规则和真机均需另验。</p><label><input id="missing" type="checkbox">只看主预览缺项</label><table><thead><tr><th>动作</th><th>具体阶段设计</th><th>制作状态</th><th>首尾连接</th></tr></thead><tbody id="rows"></tbody></table></section><script>const cards=CARDS;let role='zhongli';const names={zhongli:'钟离：25组重新设计',mavuika:'玛薇卡：25组设计，主预览仍缺18组',neuvillette:'那维莱特：25组设计，主预览仍缺12组'};function render(){document.getElementById('roleTitle').textContent=names[role];const rows=cards.filter(c=>c.role===role&&(!document.getElementById('missing').checked||!c.existingMainPreview));document.getElementById('rows').replaceChildren(...rows.map(c=>{const tr=document.createElement('tr');for(const v of [c.label,c.phases.join(' → '),c.status,c.continuation]){const td=document.createElement('td');td.textContent=v;tr.append(td)}return tr}));}document.querySelectorAll('[data-role]').forEach(b=>b.onclick=()=>{role=b.dataset.role;document.querySelectorAll('[data-role]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));document.getElementById('viewer').src=role+'/player.html';render()});document.getElementById('missing').onchange=render;render();</script></html>'''
(O/'index.html').write_text(page.replace('CARDS',json.dumps(cards,ensure_ascii=False)),encoding='utf8')
assert len(cards)==75 and all(len([c for c in cards if c['role']==r])==25 for r in books)
print('75 design cards, 4 body samples, 16 exact reconstructions; old master actions unchanged')
import runpy
runpy.run_path(str(R/'work/clarify_design_preview_20261014.py'))
if (O/'reaction-chain-20261014.json').exists():
 runpy.run_path(str(R/'work/build_reaction_chain_20261014.py'))
 runpy.run_path(str(R/'work/clarify_design_preview_20261014.py'))
 runpy.run_path(str(R/'work/adopt_reaction_preview_20261014.py'))
