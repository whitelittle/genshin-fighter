"""Validate and package the complete currently available V4 tree for resumability."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from PIL import Image
import json,hashlib
V=Path(__file__).resolve().parents[1];R=V.parent;j=json.loads((V/'design/ACTION_QUEUE_20261009.json').read_text());sources=[s for s in j['generation_specs'] if s.get('output')]
lines=['# V4原隐藏14人续作检查点','',f'本批实际新增{len(sources)}张源图、{sum(s["grid"][0]*s["grid"][1] for s in sources)}个显示姿势。14×25共350项设计/素材覆盖已建表，不能把设计覆盖等同制作完成。正式验收0。','', '已重新读取V4标准、卡片及队列，并从不完整V3 Git归档恢复新版统一标准文本；原artlib/painter未恢复，当前拟合明确为离线诊断。','', '|源图|状态|图元数|触边姿|','|---|---|---|---|']
for s in sources:
 p=R/s['output'];Image.open(p).load();assert hashlib.sha256(p.read_bytes()).hexdigest()==s['sha256'];assert (R/s['prompt_file']).is_file();f=s.get('fitting',{});lines.append(f'|{s["id"]}|{s["status"]}|'+','.join(map(str,f.get('rect_counts',[])))+'|'+','.join(map(str,f.get('source_edges',[])))+'|')
lines.extend(['','本批身体源图尚未配套独立武器/助手/特效，真实握点、世界锚点、碰撞和逻辑tick均待标定。火神walk-v3无眼镜但光晕与交替步态不合格，保留待修。显示帧、诊断图元、GIF播放均不代表客户端实现、模拟器或真机验证。','', '接续从V4/CONTINUE.md开始，读取design/ACTION_QUEUE_20261009.json的pending或缺层条目。完整提示词、源图哈希、拟合矩形与深浅底证据包含在包中。'])
if j.get('generation_failures'):lines.extend(['','实际生成错误：',json.dumps(j['generation_failures'],ensure_ascii=False)])
report=R/'V4_All_Characters_Progress.md';report.write_text('\n'.join(lines)+'\n');p=V/'PROGRESS.md';body=p.read_text();marker='# V4原隐藏14人续作检查点'
if marker in body:body=body.split(marker)[0].rstrip()
p.write_text(body.rstrip()+'\n\n'+report.read_text())
files=[p for p in V.rglob('*') if p.is_file() and '__pycache__' not in str(p)]+[report,R/'V4_All_Characters_Action_Preview.html'];files=[p for p in files if p.is_file()]
archive=R/'V4_All_Characters_Checkpoint.zip'
with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=3) as z:
 for p in files:z.write(p,p.relative_to(R))
with ZipFile(archive) as z:assert z.testzip() is None
print('checkpoint',len(files),'files',archive.stat().st_size,'bytes')
