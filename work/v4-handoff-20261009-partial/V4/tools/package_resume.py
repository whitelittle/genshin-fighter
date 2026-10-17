"""Package this resume batch as an overlay on the restored V4 checkpoint."""
from pathlib import Path
import json, base64, zipfile, hashlib, subprocess, sys
V=Path(__file__).resolve().parents[1]
R=V.parent
OUT=R.parent/'deliverables'
OUT.mkdir(exist_ok=True)
IDS=['aratakiitto-light2-body-v2','zhongli-light3-body-v1','yaemiko-light3-body-v1']
subprocess.run([sys.executable,str(V/'tools/audit_source_batch.py')],check=True)
q=json.loads((V/'design/ACTION_QUEUE_20261009.json').read_text())
data={}; rows=[]
for s in q['generation_specs']:
    if not s.get('output'): continue
    assert hashlib.sha256((R/s['output']).read_bytes()).hexdigest()==s['sha256']
    if s['id'] not in IDS: continue
    folder=V/'evidence/actions-20261009'/s['id']
    fit=json.loads((folder/'fit.json').read_text())
    rows.append('|'+s['id']+'|'+','.join(map(str,fit['rect_counts']))+'|'+','.join(map(str,s['fitting']['source_edges']))+'|待修|')
    data[s['id']]={'counts':fit['rect_counts'],'edges':s['fitting']['source_edges'],
        'frames':[[base64.b64encode((folder/f'source-cell-{i}.png').read_bytes()).decode(),
                   base64.b64encode((folder/f'optimized-{i}.png').read_bytes()).decode()] for i in range(4)]}
assert len(data)==3 and len(q['generation_specs'])==18
report='''# V4 接续进度｜2026-10-09

已读取AGENTS、CONTINUE、README、PROGRESS、角色创建规范、画风锁、工作流核对、14人队列、V3新版统一标准及本批角色设计卡。

本轮新增一斗轻攻二段修正版、钟离轻攻三段、八重神子轻攻三段，共12个显示姿势。每组首版和背景编辑版均保留，共6张源图。使用内置图像生成；完整提示词、参考职责、源图SHA256和诊断拟合/播放证据保留。未使用付费API，未遇到额度错误。

一斗两轮体型、头身与衣装确有差异。本轮使用V4原母版作为候选身份依据，并建立14人的参考路径与SHA256锁。固定参考不保证生成器不漂移，发型、肩宽、头身、衣摆和饰件仍需人工对照。没有将原母版冒称为用户已认可结果。

透明通道与实际浅底合成已核实。初看展示图将透明区域的RGB底色误判为背景，随后又请求了背景编辑，完整历史保留；后续以alpha及真实合成检查为准。

|源图|四姿离线图元|触边姿|状态|
|---|---|---|---|
'''+ '\n'.join(rows)+'''

三组均有2x2格间边界问题，机械等格切分产生截断/相邻残点；图元超过760历史身体参考。未以裁切居中或缩小身体掩盖问题，均标needs_correction。实际身体尺度、脚底/握点、独立武器/助手/特效仍待标定和制作。

完成固定格切帧、共享记录调色板诊断拟合、深浅底对照、GIF播放和矩形精确重建。拟合为premultiplied-alpha BOX、OKLab最近色、1px轮廓及扫描矩形合并；原V3 artlib/painter未恢复，不是正式编码或运行时验收。源图审计核对18组源图和14人参考哈希全部匹配。

新增正式验收0；未接入逻辑判定、回滚、池/双人峰值，未做模拟器或真机验证。V3稳定E客户端未修改。火神无眼镜、E收招保留骑车制动，芙宁娜沿用用户参考的沙龙三成员朝右侧视。

下一断点：按原母版保留外观，先重做整张留白排版，消除格间污染；再在相同身体尺度优化色块，标脚底/握点，继续轮转缺失轻攻三段和基础动作。

本增量包叠加V4_All_Characters_Checkpoint.zip第1版。入口为V4/CONTINUE.md与本报告；队列含本轮3条待修源图。不得重新执行continue_actions.py prepare，以免重置进度。
'''
(OUT/'V4_Resume_20261009.md').write_text(report)
(V/'evidence/resume-20261009/REPORT.md').write_text(report)
preview=OUT/'V4_Resume_Preview.html'
text=preview.read_text()
start=text.index('const DATA=')+len('const DATA=')
end=text.index(';const sel=',start)
text=text[:start]+json.dumps(data,ensure_ascii=False,separators=(',',':'))+text[end:]
preview.write_text(text)
archive=OUT/'V4_Resume_20261009.zip'
old=[]
if archive.exists():
    with zipfile.ZipFile(archive) as z: old=z.namelist()
files={name:R/name for name in old if name!='V4_Resume_Preview.html'}
for sub in ['docs','prompts/resume-20261009','assets/resume-history-20261009','evidence/resume-20261009']:
    for p in (V/sub).rglob('*'):
        if p.is_file(): files[str(p.relative_to(R))]=p
for s in q['generation_specs']:
    if s['id'] in IDS:
        files[s['output']]=R/s['output']
        for p in (V/'evidence/actions-20261009'/s['id']).rglob('*'):
            if p.is_file(): files[str(p.relative_to(R))]=p
for path in ['AGENTS.md','CONTINUE.md','PROGRESS.md','design/ACTION_QUEUE_20261009.json',
             'design/IDENTITY_REFERENCE_LOCK.json','tools/audit_source_batch.py','tools/package_resume.py']:
    files['V4/'+path]=V/path
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for name,p in sorted(files.items()):
        if p.is_file():z.write(p,name)
    z.write(preview,'V4_Resume_Preview.html')
with zipfile.ZipFile(archive) as z:
    assert len(json.loads(z.read('V4/design/ACTION_QUEUE_20261009.json'))['generation_specs'])==18
    for s in q['generation_specs']:
        if s['id'] in IDS: assert hashlib.sha256(z.read(s['output'])).hexdigest()==s['sha256']
print(json.dumps({'source_hashes_valid':18,'new_poses':12,'files':[str(p) for p in OUT.iterdir()]},ensure_ascii=False))
