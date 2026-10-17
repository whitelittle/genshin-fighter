"""Validate and package the contact-candidate delta over the prior V4 checkpoint."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from PIL import Image
import hashlib, json

V=Path(__file__).resolve().parents[1]
root=V.parent
queue_path=V/'design/ROSTER_JOBS.json'
jobs=json.loads(queue_path.read_text())
current=[]
for job in jobs['jobs']:
    for field in ('E_integrated_candidate','E_assistant_candidate','E_prop_candidate'):
        r=job.get(field)
        if not r:continue
        src=root/r['output'];assert src.exists()
        Image.open(src).load();assert hashlib.sha256(src.read_bytes()).hexdigest()==r['sha256']
        current.append((job['character'],field,r))
        fit=root/r['fitting']['report'];meta=json.loads(fit.read_text())
        for n,frame in enumerate(meta['frames']):
            for prefix,hashfield in (('source-cell','source_sha256'),('optimized','fit_sha256')):
                p=fit.parent/f'{prefix}-{n}.png'
                try:Image.open(p).load()
                except Exception:
                    if prefix!='source-cell':raise
                    im=Image.open(src).convert('RGBA');w,h=im.size
                    im.crop(((n%2)*w//2,(n//2)*h//2,(n%2+1)*w//2,(n//2+1)*h//2)).save(p)
                    frame[hashfield]=hashlib.sha256(p.read_bytes()).hexdigest()
                    Image.open(p).load()
                    fit.write_text(json.dumps(meta,ensure_ascii=False,indent=2))
                assert hashlib.sha256(p.read_bytes()).hexdigest()==frame[hashfield],p

rows=[]
for key,field,r in current:
    fit=json.loads((root/r['fitting']['report']).read_text())
    touched=[str(i+1) for i,frame in enumerate(fit['frames']) if (
        any(frame['edge_alpha32'].values()) if isinstance(frame['edge_alpha32'],dict)
        else frame['edge_alpha32'])]
    rows.append(f"| {key} · {field} | {', '.join(map(str,fit['rect_counts']))} | {', '.join(touched) or '无'} |")
report=root/'V4_Contact_Batch_Report.md'
report.write_text('\n'.join([
    '# V4接触与持物小样（2026-10-09续作）','',
    '本增量共18张新增源图，覆盖玛薇卡骑车合成v1—v5及单独车体、娜维娅伞枪、阿蕾奇诺镰刀、克洛琳德枪剑、绫华刀鞘、达达利亚双水刃、那维莱特手杖、丝柯克剑、芙宁娜三沙龙成员、一斗阿丑v1/v2、钟离岩柱和八重神子单株樱。源图、全部提示词、SHA256、历史拒收版、切帧与播放证据均存包。',
    '本包是上一版完整V4检查点的增量；旧V4源图仍由先前检查点保存。本包的正式验收数为0。','',
    '| 角色与层 | 离线单帧图元数 | 源格边缘接触姿（1起） |','|---|---|---|',*rows,'',
    '四姿身体与持物合成采用角色已有19色身体调色板、相同高度做离线近似拟合；不是V3原编码器。每帧矩形重建检查精确，但细节和边界仍不合格。所有合成组至少一帧超过身体760目标，不能算运行预算通过。',
    '独立助手/车体使用16色、64像素单层检查，也不能从单层数字推断双人并发。玛薇卡车体四相变化过小，单层约1600图元；v3误把第四姿设计为离车站定，现已更正为骑乘制动，后续下车另设转换。v4第一姿还带裁掉的半个车轮，v5已清除；但第1→2姿缺上车过渡。v5四帧分别1552/2400/2471/2185图元且均碰源格边，不能验收。所有版本无眼镜。',
    '一斗阿丑v1错误借用雷电三勾玉，v2已改金色角饰。芙宁娜三伙伴保持章鱼、海马、蟹各一，但尺寸、槽位、水效未合成。温迪此前已有弓的轻攻旧源图；E本来为空手风域，不在E硬加弓。',
    '钟离岩柱与八重单株樱分别是固定世界位置的独立道具候选，不能从四姿推断对象生命周期。岩柱第1、3姿源格边缘接触，樱无触边；单层最大图元分别734/531，低于历史850参考，但世界锚点与双人并发预算未测。',
    '握柄/座位/脚底/刀尖真实像素锚点、动作tick、判定盒、物件出入手事件、双人池和缓冲均待完成。无模拟器、真机或用户验收。未遇到图像额度错误；一次生成请求因传输关闭重试成功。V3认可E没有修改。','',
    '下一断点：返修越格源图、固定同物理握点与出入场；专门优化源图细节和身体/道具的合成策略后再标定锚点；继续跨角色25组与Q/投技。'
])+'\n')
progress=V/'PROGRESS.md'
marker='# V4接触与持物小样｜2026-10-09续作'
body=progress.read_text()
if marker not in body:
    progress.write_text(body.rstrip()+'\n\n'+report.read_text().replace('# V4接触与持物小样（2026-10-09续作）',marker,1))
else:
    prefix=body.split(marker,1)[0].rstrip()
    progress.write_text(prefix+'\n\n'+report.read_text().replace('# V4接触与持物小样（2026-10-09续作）',marker,1))

files=[report,V/'PROGRESS.md',queue_path,V/'design/cards/mavuika.md',V/'design/cards/mavuika.json',V/'docs/REPRESENTATIVE_CONTACTS.md',V/'design/research_roster.py',V/'design/rebuild.py',V/'tools/fit_composite_contacts.py',V/'tools/fit_assistant_candidates.py',Path(__file__),V/'evidence/E-composite-fit-summary.json',V/'evidence/E-assistant-fit-summary.json']
for folder in ('composite-candidates','assistant-candidates','prop-candidates'):
    files.extend((V/'assets'/folder).glob('*.png'))
files.extend((V/'prompts/continuation-20261008').glob('*composite-v*.txt'))
files.extend((V/'prompts/continuation-20261008').glob('*assistant-v*.txt'))
files.extend((V/'prompts/continuation-20261008').glob('*prop-v*.txt'))
for pattern in ('*-E-composite-review','*-E-assistant-review','*-E-prop-review'):
    for folder in (V/'evidence').glob(pattern):files.extend(folder.glob('*'))
files=list(dict.fromkeys(files))
for p in files:assert p.is_file(),p
archive=root/'V4_Contact_Batch_20261008.zip'
with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=3) as z:
    for p in files:z.write(p,p.relative_to(root))
with ZipFile(archive) as z:assert z.testzip() is None
print('validated',len(current),'current groups,',len(files),'files,',archive.stat().st_size,'bytes')
