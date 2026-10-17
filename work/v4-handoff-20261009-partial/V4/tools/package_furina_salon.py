"""Validate current Furina source/evidence and package the correction series."""
from pathlib import Path
from PIL import Image
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json
V=Path(__file__).resolve().parents[1];root=V.parent
jobs=json.loads((V/'design/ROSTER_JOBS.json').read_text());job=next(j for j in jobs['jobs'] if j['character']=='furina')
e=V/'evidence'/job['E_assistant_evidence_batch'];summary=json.loads((e/'summary.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for rec in job['E_individual_assistants']:
    src=root/rec['output'];Image.open(src).load();assert sha(src)==rec['sha256']
    meta_path=root/rec['fitting']['report'];m=json.loads(meta_path.read_text())
    for n,f in enumerate(m['frames']):
        for prefix,field in [('source-cell','source_sha256'),('optimized','fit_sha256')]:
            p=meta_path.parent/f'{prefix}-{n}.png'
            try:Image.open(p).load()
            except Exception:
                if prefix!='source-cell':raise
                im=Image.open(src).convert('RGBA');w,h=im.size;cols,rows=rec.get('grid',[2,2]);cuts=rec.get('source_cuts_x',[round(i*w/cols) for i in range(cols+1)])
                im.crop((cuts[n%cols],n//cols*h//rows,cuts[n%cols+1],(n//cols+1)*h//rows)).save(p)
                f[field]=sha(p);meta_path.write_text(json.dumps(m,ensure_ascii=False,indent=2))
                sm=next(x for x in summary['members'] if x['member']==rec['member']);sm['frames'][n][field]=f[field]
            assert sha(p)==f[field],p
(e/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
rows=['|成员|单层四姿图元|源格接触姿|','|---|---|---|']
for m in summary['members']:
    touched=[str(n+1) for n,f in enumerate(m['frames']) if any(f['edge_alpha32'].values())]
    rows.append('| '+m['member']+' | '+', '.join(map(str,m['rect_counts']))+' | '+(', '.join(touched) or '无')+' |')
totals=[sum(m['rect_counts'][n] for m in summary['members']) for n in range(4)]
report=root/'V4_Furina_Salon_Correction.md'
report.write_text('\n'.join([
    '# 芙宁娜沙龙成员侧视更正','',
    '本次侧视要求只针对三位沙龙成员。已按用户参考保留身份，再生成统一朝右的侧视母版与三位各四姿。此前正面动作版退回身份研究参考；角色身体镜头未据此改动。更正系列累计新增14张源图（含拒收/未选版），另保留旧整组三人v1。此次侧视新增4张源图。','',
    '当前选用谢贝蕾妲、乌瑟、海薇玛side-v1。近侧眼与朝右攻击肢体可读，远侧肢体遮挡；海薇玛侧视版不带大光晕。12帧在实际透明间隙切分后无源格触边。分帧保持名义等宽格根位置，未逐帧重新居中。','',*rows,'',
    '每只助手跨四姿使用固定尺度与坐标变换：不透明主体目标高度28px，48×48画布，共享16色RGB和3档alpha。三助手图元合计：'+', '.join(map(str,totals))+'。不含身体与水效，尚未通过整场预算；此拟合是离线诊断，不是V3编码器或客户端验证。','',
    '已保存源图完整提示词与SHA256、12帧源/拟合证据、矩形重建检查、逐只GIF及48tick合成播放。编排为起手0—18、有效18—24、收招24—48，18tick一次共享释放标记。GIF近似显示60Hz；逻辑伤害、判定、池、回滚及真机均未验收。','',
    '待修：乌瑟有效姿肢体数量与形体连续性；水效三枝起点与各助手出点对齐；身体头顶残点；助手返回动作和实测世界锚点。正式验收0。','',
    '之前海薇玛v3请求曾被工具拒绝，未生成源图，错误与完整提示词已留存；本次侧视请求成功。未遇到额度限制，未切换付费API。另保留两张未选的一斗接触参考，避免丢失已生成素材。'
])+'\n')
progress=V/'PROGRESS.md';body=progress.read_text();marker='# 芙宁娜沙龙成员侧视更正'
if marker in body:body=body.split(marker)[0].rstrip()
progress.write_text(body.rstrip()+'\n\n'+report.read_text())
files=[report,progress,V/'design/ROSTER_JOBS.json',V/'docs/FURINA_SALON_IDENTITY_LOCK.md',V/'docs/FURINA_COMBAT.md',V/'docs/FURINA_ACTIONS.md',V/'design/references/furina-salon-user-reference-20261009.png',V/'design/furina-E-sync-candidate.json',V/'tools/fit_furina_members.py',V/'tools/preview_furina_sync.py',Path(__file__)]
files.extend((V/'assets/assistant-candidates').glob('furina*.png'));files.extend((V/'prompts/continuation-20261008').glob('furina*assistant*.txt'));files.extend(e.rglob('*'))
for kind in ['furina-E-review','furina-E-fx-review']:
    files.extend((V/'evidence'/kind).glob('optimized-*.png'));files.append(V/'evidence'/kind/'fit.json')
for other in jobs['jobs']:
    if other['character']=='aratakiitto':
        for rec in other.get('E_contact_references',[]):
            for key in ['output','prompt_file']:
                if key in rec:files.append(root/rec[key])
files=[p for p in dict.fromkeys(files) if p.is_file()]
for p in files:
    if p.suffix=='.png':Image.open(p).load()
a=root/'V4_Furina_Salon_Correction.zip'
with ZipFile(a,'w',ZIP_DEFLATED,compresslevel=3) as z:
    for p in files:z.write(p,p.relative_to(root))
with ZipFile(a) as z:assert z.testzip() is None
print('validated',len(files),'files',a.stat().st_size,'bytes; three-member totals',totals)
