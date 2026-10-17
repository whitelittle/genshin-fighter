"""Inventory current candidate sources without conflating them with accepted actions."""
from pathlib import Path
import hashlib,json
from collections import Counter
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
R=ROOT/'work/v4-handoff-20261009-partial'
V=R/'V4'
OUT=V/'evidence/current-review-20261009'
OUT.mkdir(parents=True,exist_ok=True)
queue=json.loads((V/'design/FULL_DELIVERY_CURRENT_20261009.json').read_text(encoding='utf-8'))
actual=json.loads((V/'evidence/full-delivery-20261009/ACTUAL_MANIFEST.json').read_text(encoding='utf-8'))
visual=json.loads((V/'evidence/full-delivery-20261009/VISUAL_ISSUES.json').read_text(encoding='utf-8'))['issues']
records={x['character']+'.'+x['group']:x for x in actual['records']}
entries=[];by={};failures=[]
for e in queue['entries']:
    key=e['character'];by.setdefault(key,Counter())
    by[key]['planned']+=1
    a=records.get(e['actionId'],{})
    paths=list(e.get('existing_sources',[]))
    for p in [e.get('new_source'),a.get('output')]:
        if p and p not in paths:paths.append(p)
    checked=[]
    for name in paths:
        if not isinstance(name,str):continue
        p=R/name;item={'path':name,'exists':p.is_file()}
        if p.is_file():
            data=p.read_bytes();item['sha256']=hashlib.sha256(data).hexdigest()
            with Image.open(p) as image:
                item['size']=list(image.size);item['alpha_extrema']=list(image.convert('RGBA').getchannel('A').getextrema())
            if name==a.get('output'):
                item['recorded_hash_matches']=item['sha256']==a['sha256']
                if not item['recorded_hash_matches']:failures.append(name)
        else:failures.append(name)
        checked.append(item)
    present=any(x['exists'] for x in checked)
    by[key]['body_candidate_groups']+=int(present)
    by[key]['no_body_source_groups']+=int(not present)
    by[key]['new_full_delivery_groups']+=int('output' in a)
    peaks=a.get('rect_counts',[])
    by[key]['historical_budget_exceed_groups']+=int(bool(peaks) and max(peaks)>760)
    by[key]['reported_edge_groups']+=int(bool(a.get('source_edges')))
    issues=visual.get(a.get('id',''),[])
    by[key]['reported_visual_issue_groups']+=int(bool(issues))
    entries.append({'actionId':e['actionId'],'character':key,'group':e['group'],
                    'source_candidates':checked,'required_layers':e.get('required_layers',[]),
                    'layer_completeness':'not visually verified','diagnostic_rect_counts':peaks,
                    'reported_edge_frames':a.get('source_edges',[]),'reported_visual_issues':issues,
                    'runtime':False,'user_accepted':False,'anatomy_composition_motion_fx_review':'pending'})
assert len(entries)==350 and len(by)==14 and all(c['planned']==25 for c in by.values())
assert not failures,failures
report={'scope':'14 characters / 350 planned groups','counts':by,'entries':entries,
        'file_audit_passed':True,'formal_acceptance':0,'game_integrated':0,
        'budget_note':'760 is historical single-body diagnostic reference, not global or paired runtime limit',
        'visual_note':'Recorded issues imported, not fresh visual acceptance; existing source does not prove complete layers'}
(OUT/'inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# V4 当前素材核查','', '2026-10-09。文件存在性、可读性与本轮63张源图哈希已核对；视觉校验待逐批执行。','',
       '|角色|计划组|已有身体候选组|无身体源图组|本轮新增组|诊断超760组|记录触边组|记录语义/分层问题组|',
       '|---|---:|---:|---:|---:|---:|---:|---:|']
for k,c in by.items():lines.append('|'+k+'|'+ '|'.join(str(c[x]) for x in ['planned','body_candidate_groups','no_body_source_groups','new_full_delivery_groups','historical_budget_exceed_groups','reported_edge_groups','reported_visual_issue_groups'])+'|')
totals=Counter()
for c in by.values():totals.update(c)
lines+=['',f"合计已有身体候选 {totals['body_candidate_groups']}/350 组；其中 {totals['new_full_delivery_groups']} 组来自本轮交接。",'',
        '源图存在不代表肢体、动作、分层、挂点或预算通过。旧素材与新版并存，不自动选择旧候选。', '',
        '优先工作：八重神子蹲重身体误扑→改低位指印；钟离空轻误拳击→明确枪术握点；再修持物手型和混层。另对待机/步态单独核查，避免旧抽搐、浮空和错误补帧回流。', '',
        '所有350项逐条证据见 [inventory.json](inventory.json)。助手、武器、特效与配对投技需继续独立核查，不根据身体文件推断齐全。']
(OUT/'素材核查.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'totals':totals,'per_character':by},ensure_ascii=False,indent=2))
