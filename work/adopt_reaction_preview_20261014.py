from pathlib import Path
import json,shutil,re
R=Path(__file__).resolve().parents[1];O=R/'outputs/three-role-redesign-20261014';B=R/'outputs/three-role-basic-20261013'
def prefix_refs(value,prefix):
 if isinstance(value,list):return [prefix_refs(x,prefix) for x in value]
 if isinstance(value,dict):return {k:(prefix+v if k in ['file','source','rectData'] and isinstance(v,str) else prefix_refs(v,prefix)) for k,v in value.items()}
 return value
summaries={}
for role in ['mavuika','neuvillette']:
 D=B/role;H=D/'history/reaction-adoption-20261014';H.mkdir(parents=True,exist_ok=True)
 for name in ['actions.json','action-data.js','current-status.json','player.js','player.html']:
  if not(H/name).exists():shutil.copy2(D/name,H/name)
 bank=json.loads((D/'actions.json').read_text(encoding='utf8'));candidate=json.loads((O/role/'actions.json').read_text(encoding='utf8'))
 for key in ['hit_knockdown','wakeup']:bank[key]=prefix_refs(candidate[key],f'../../three-role-redesign-20261014/{role}/')
 for mode in ['frames','sourceFrames']:bank['wakeup'][mode][-1]=dict(bank['idle'][mode][0])
 (D/'actions.json').write_text(json.dumps(bank,ensure_ascii=False,indent=2),encoding='utf8');(D/'action-data.js').write_text('window.NEUVILLETTE_ACTIONS='+json.dumps(bank,ensure_ascii=False)+';',encoding='utf8')
 states=sum(len(g['frames']) for g in bank.values());summaries[role]={'actions':len(bank),'states':states}
 status=json.loads((D/'current-status.json').read_text(encoding='utf8'));status.update(actions=len(bank),mainDisplayStates=states,designDirectionAcceptedByUser=True,reactionChainCandidateAdded=True,artAccepted=False,runtimeIntegrated=False,deviceVerified=False);(D/'current-status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf8')
 s=(D/'player.html').read_text(encoding='utf8');s=re.sub(r'V9累计\d+组/\d+显示状态候选',f'V9累计{len(bank)}组/{states}显示状态候选',s);s=re.sub(r'action-data\.js(?:\?[^"\s]*)?', 'action-data.js?v=reaction-adopt-20261014',s);s=re.sub(r'player\.js(?:\?[^"\s]*)?', 'player.js?v=reaction-adopt-20261014',s);(D/'player.html').write_text(s,encoding='utf8')
 s=(D/'player.js').read_text(encoding='utf8');s=s.replace("){const g=document.createElement('div');g.className='group';g.textContent=title;", "){if(!keys.some(key=>bank[key]))continue;const g=document.createElement('div');g.className='group';g.textContent=title;")
 s=s.replace("for(const key of keys){const b=document.createElement('button');", "for(const key of keys){if(!bank[key])continue;const b=document.createElement('button');")
 (D/'player.js').write_text(s,encoding='utf8')
index=B/'index.html';s=index.read_text(encoding='utf8').replace('那维莱特 · 13组 / 67姿','那维莱特 · 15组 / 79姿').replace('玛薇卡 · 7组 / 34姿','玛薇卡 · 9组 / 46姿');index.write_text(s,encoding='utf8')
cards=json.loads((O/'all-design-cards.json').read_text(encoding='utf8'))
for c in cards:
 c['designDirectionAcceptedByUser']=True
 if c['role'] in summaries and c['actionId'] in ['hit_knockdown','wakeup']:
  c.update(existingMainPreview=True,bodySampleAvailable=True,status='新增身体候选已进入主预览与新稿页；倒地边界共用，人体/武器/美术与正式战斗待验')
for role in ['zhongli','mavuika','neuvillette']:(O/f'{role}-design-v2.json').write_text(json.dumps([c for c in cards if c['role']==role],ensure_ascii=False,indent=2),encoding='utf8')
(O/'all-design-cards.json').write_text(json.dumps(cards,ensure_ascii=False,indent=2),encoding='utf8')
coverage=json.loads((O/'coverage.json').read_text(encoding='utf8'));coverage['designDirectionAcceptedByUser']=True;coverage['bodySamples']={'zhongli':2,'mavuika':3,'neuvillette':3};coverage['artAccepted']=False
for role,d in coverage['roles'].items():
 if role in summaries:d['existingMainPreviewGroups']=summaries[role]['actions'];d['missingMainPreview']=[c['actionId'] for c in cards if c['role']==role and not c['existingMainPreview']]
(O/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2),encoding='utf8')
index=O/'index.html';s=index.read_text(encoding='utf8');s=s.replace('火神主预览7/25组，水龙13/25组；缺项分别18、12组','火神主预览9/25组，水龙15/25组；缺项分别16、10组').replace('玛薇卡：25组文字设计，主预览仍缺18组','玛薇卡：25组文字设计，主预览仍缺16组').replace('那维莱特：25组文字设计，主预览仍缺12组','那维莱特：25组文字设计，主预览仍缺10组')
s=re.sub(r'const cards=.*?;let role=',lambda m:'const cards='+json.dumps(cards,ensure_ascii=False)+';let role=',s,flags=re.S);index.write_text(s,encoding='utf8')
(O/'reaction-adoption-20261014.json').write_text(json.dumps({'mainPreview':summaries,'acceptedDesignDirection':True,'artAccepted':False,'runtimeIntegrated':False,'deviceVerified':False,'scope':'independent body previews; no game rules or GIA'},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(summaries,ensure_ascii=False))
