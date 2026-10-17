"""Inspect physical body sources separately from fitting and acceptance gaps."""
from pathlib import Path
from collections import Counter
import json
R=Path(__file__).resolve().parent/'v4-handoff-20261009-partial';V=R/'V4'
p=V/'design/CODEX_CURRENT_OVERLAY_20261009.json'
d=json.loads(p.read_text(encoding='utf-8'))
labels={'airlight':'空轻','airheavy':'空重','Q':'Q','throw':'投技','victim':'被投','forwarddash':'前冲','backdash':'后撤','crouch':'蹲下','crouchguard':'蹲防','victory':'胜利','defeat':'败北','crouchlight':'蹲轻','hit_knockdown':'受击/倒地','wakeup':'起身'}
names=dict(zip(['furina','zhongli','mavuika','venti','kamisatoayaka','tartaglia','aratakiitto','yaemiko','arlecchino','wanderer','neuvillette','clorinde','navia','skirk'],['芙宁娜','钟离','玛薇卡','温迪','神里绫华','达达利亚','荒泷一斗','八重神子','阿蕾奇诺','流浪者','那维莱特','克洛琳德','娜维娅','丝柯克']))
missing=[];files_missing=[];physical_groups=0;counts=Counter();per={k:[] for k in names};fit_gaps=[];pending=[]
for e in d['entries']:
    paths=list(e.get('existing_sources') or [])
    if e.get('new_source'):paths.append(e['new_source'])
    paths.extend(r['source'] for r in e.get('codex_sources',[]))
    valid=[]
    for source in set(paths):
        if (R/source).is_file():valid.append(source)
        else:files_missing.append({'actionId':e['actionId'],'source':source})
    if valid:physical_groups+=1
    else:
        missing.append(e['actionId']);group=e['actionId'].split('.')[1]
        counts[group]+=1;per[e['character']].append(labels.get(group,group))
    if e.get('codex_sources') and not e.get('codex_preferred_candidate'):
        fit_gaps.append({'actionId':e['actionId'],'sources':[r['id'] for r in e['codex_sources']],
                         'reason':'No eligible fitted current candidate; extraction failure or explicit pending status'})
    pending.extend({'actionId':e['actionId'],'source':r['id'],'status':r['status']} for r in e.get('codex_sources',[]) if r['status'].startswith(('needs_','requires_','deferred')))
common=[k for k,n in counts.items() if n==14]
result={'date':'2026-10-10','planned_body_groups':350,'physical_body_source_groups':physical_groups,
        'missing_body_groups':missing,'missing_by_action':dict(counts),'common_missing_actions':common,
        'manifest_paths_missing_on_disk':files_missing,'new_body_groups_without_eligible_fit':fit_gaps,
        'explicit_pending_sources':pending,'runtime_integrated':0,'accepted':0,
        'scope':'Body-group inventory only; additional layers and semantic acceptance are separate gates'}
OUT=V/'evidence/codex-batch-20261009'
(OUT/'MATERIAL_GAPS_20261010.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# V4 素材缺口核查','', '更新：2026-10-10。逐项检查源图实物；身体源图存在≠动作完成。','',
       f'350组身体计划中，{physical_groups}组有实际源图，{len(missing)}组无身体源图；清单引用但磁盘不存在的路径{len(files_missing)}个。正式验收0，接入0。','',
       '## 逐角色源图缺口','', '|角色|缺身体动作组|内容|','|---|---:|---|']
for ch,groups in per.items():lines.append(f'|{names[ch]}|{len(groups)}|'+ '、'.join(groups)+'|')
lines+=['','## 已有但不能直接接入','',
        f'本轮新增身体组中，{len(fit_gaps)}组没有符合门禁的拟合候选（不是全部历史候选的美术失败总数）。','']
for gap in fit_gaps:lines.append('- '+gap['actionId']+'：'+', '.join(gap['sources']))
lines+=['','全体候选仍缺正式四项视觉验收、精确世界root/脚底/握点、逻辑tick及判定接入。部分粗锚点诊断不能当正式标定。','',
        '## 分层与合成缺口','',
        '身体350组统计不包含武器、助手、投射物、特效和演出背景；不能从身体覆盖率推出这些层已齐全。当前尚无任一角色完成逐招分层/接触/释放/回收/中断全链验收。','',
        '- 芙宁娜：三助手各自身份与动作、抱持/释放接触、返回、独立水效与同一助手去重仍需逐招闭环。','- 玛薇卡：身体与摩托/武器分层、制动仍在车上及上下车连续性未闭环。','- 绫华：刀/鞘独立层、拔刀/归鞘握点、起身回待机衔接待验证。','- 钟离/一斗/克洛琳德/娜维娅/丝柯克/那维莱特等：枪、刀/棒、枪剑、伞枪、晶枪、手杖已有资料或局部候选不等于全动作挂点完成。','- 八重：粉色狐灵有四姿及研究合成；释放/命中/返回/主人中断规则未接入。额外刃形特效已撤除，不列为必须补回的缺口。','- 全体Q与投技：身体源图仍缺，命中确认演出/双人接触与被投配对也未验证。','',
        '## 推进顺序','',
        '先补基础蹲下/蹲防等独立身体候选，继续修提取失败项；同时精校绫华世界root与刀鞘衔接。随后专属分层小样，再Q/成对投技。安全拒绝项保留原记录暂缓，不以换通路规避。','',
        '[机器可读逐项清单](MATERIAL_GAPS_20261010.json) · [源图及完整提示词](成果索引.md)']
(OUT/'素材缺口_20261010.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'physical_groups':physical_groups,'missing_groups':len(missing),'missing_by_action':dict(counts),'broken_paths':len(files_missing),'new_groups_no_eligible_fit':[r['actionId'] for r in fit_gaps]},ensure_ascii=False))
