"""Overlay new candidates on the original 350-group handoff, without replacing it."""
from pathlib import Path
import json,re,hashlib
from collections import Counter
from v4_candidate_policy import offline_export_eligible
R=Path(__file__).resolve().parent/'v4-handoff-20261009-partial';V=R/'V4'
base=json.loads((V/'design/FULL_DELIVERY_CURRENT_20261009.json').read_text(encoding='utf-8'))
batch=json.loads((V/'evidence/codex-batch-20261009/BATCH_MANIFEST.json').read_text(encoding='utf-8'))
indexed={e['actionId']:e for e in base['entries']}
for e in indexed.values():e['codex_sources']=[]
for r in batch['records']:
    m=re.fullmatch(r'(\w+)-(\w+)-body-v(\d+)',r['id'])
    if not m:continue
    key=m[1]+'.'+m[2]
    if key not in indexed:continue
    e=indexed[key]
    source=R/r['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==r['sha256']
    item=dict(r);item['candidate_version']=int(m[3]);item['offline_fit_passed']=False
    folder=R/r['evidence_folder'] if r['evidence_folder'] else None
    if folder and (folder/'fit.json').exists():
        f=json.loads((folder/'fit.json').read_text(encoding='utf-8'))
        item['offline_fit_passed']=bool(f.get('frames')) and all(x.get('exact_reconstruction') for x in f['frames'])
        item['rect_peak']=max(x['rect_count'] for x in f['frames'])
        item['source_canvas_contact_frames']=[x.get('frame') for x in f['frames'] if x.get('full_canvas_boundary_contact')]
    e['codex_sources'].append(item)
summaries={}
for e in indexed.values():
    ch=e['character'];summaries.setdefault(ch,Counter());c=summaries[ch];c['planned']+=1
    previous=bool(e.get('existing_sources') or e.get('new_source'))
    new=bool(e['codex_sources']);c['source_groups']+=int(previous or new)
    c['newly_covered_groups']+=int(new and not previous)
    fitted=[r for r in e['codex_sources'] if offline_export_eligible(r)]
    e['codex_preferred_candidate']=max(fitted,key=lambda r:r['candidate_version'])['source'] if fitted else None
    e['source_status_before_codex']=e.get('source_status')
    if new:e['source_status']='codex_source_candidate_requires_visual_review' if fitted else 'codex_source_candidate_requires_extraction_review'
    c['codex_source_groups']+=int(new);c['codex_fit_groups']+=int(bool(fitted))
    e['codex_visual_accepted']=False;e['codex_runtime']=False
base.update(codex_overlay=True,codex_generated_source_count=batch['generated_source_count'],
            codex_summaries=summaries,codex_game_integrated=0,codex_user_accepted=0,
            evidence_policy='Source presence and quantized reconstruction are not visual/anatomical/game acceptance; original handoff preserved')
out=V/'design/CODEX_CURRENT_OVERLAY_20261009.json'
out.write_text(json.dumps(base,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# V4 当前动作增量进度','','原350项交接表保留；此表叠加本轮源图与拟合，候选不是角色完成。','',
       '|角色|计划组|当前有身体候选组|本轮覆盖组|本轮拟合通过组|本轮补齐原缺图组|',
       '|---|---:|---:|---:|---:|---:|']
for ch,c in summaries.items():lines.append('|'+ch+'|'+ '|'.join(str(c[k]) for k in ['planned','source_groups','codex_source_groups','codex_fit_groups','newly_covered_groups'])+'|')
total=sum(c['source_groups'] for c in summaries.values())
lines+=['',f'当前 {total}/350 组有身体候选；源图总数包含历史/返修/助手/特效。正式角色验收0，游戏接入0。','',
       '[完整增量覆盖表](../../design/CODEX_CURRENT_OVERLAY_20261009.json)',
       '[源图/提示词/哈希/状态索引](成果索引.md)', '',
       '本轮原始固定格限制已取消；人物互相遮挡、整张画布裁边、肢体/武器/助手混层依然要修。不得把拟合通过等同完整视觉与合成校验。']
(V/'evidence/codex-batch-20261009/当前动作进度.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Source candidate groups',total,'/350; generated PNGs',batch['generated_source_count'])
