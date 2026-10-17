"""Package evidence without granting art, runtime, or device acceptance."""
from pathlib import Path
import hashlib,json,html
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'outputs/clorinde-actions-20261011'
inventory=json.loads((O/'legacy-inventory.json').read_text(encoding='utf-8'))
notes={'master-v1':'帽羽碰顶，剑尖余量不足；待修',
       'master-v2':'完整主体，边距偏小；比例与拟合待检查',
       'idle-v1':'实际alpha白底合成无大面积光晕；脚位/体型待修',
       'idle-v2':'透明背景复核更正；脚位/体型待修',
       'idle-v3':'重新制图已消除大面积光晕，但帽羽碰顶；待修',
       'light1-v1':'新动作腰胯/大腿偏宽、躯干紧凑；源图待修',
       'light1-v2':'按单人母版返修腰胯/腿粗与躯干；新候选待复核'}
sources=[]
for p in sorted((O/'source').glob('*.png')):
 with Image.open(p) as im:
  im.load();alpha=im.convert('RGBA').getchannel('A')
  sources.append({'file':p.relative_to(O).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
    'size':list(im.size),'alphaExtrema':list(alpha.getextrema()),'alphaBounds':alpha.getbbox(),
    'status':notes.get(p.stem,'源图候选，待检查'),'accepted':False})
report={'character':'clorinde','scope':'source and design checkpoint; not full action delivery',
 'sources':sources,'legacyGroups':inventory['sourceCoveredGroups'],'missingLegacyGroups':inventory['missingGroups'],
 'actionsDesigned':25,'runtimeIntegrated':False,'simulator':'not run','device':'not observed',
 'verification':'PNG decode / file hashes only; art statuses stated individually'}
(O/'checkpoint.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
cards=''.join(f'<article><h2>{html.escape(Path(s["file"]).stem)}</h2><p>{html.escape(s["status"])}</p><div class="image"><img src="{s["file"]}"></div></article>' for s in sources)
rows=''.join(f'<tr><td>{r["group"]}</td><td>{html.escape(r["status"])}</td><td>{html.escape(r["legacyStatus"])}</td></tr>' for r in inventory['actions'])
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>克洛琳德制作检查</title><style>body{font:16px/1.65 system-ui;margin:24px;background:#f4f6fa;color:#202a3e;max-width:1200px}button,a{font:inherit}button{padding:8px 14px;cursor:pointer}.image{background:#ddd;padding:12px}.dark .image{background:#222638}img{max-width:100%;max-height:750px;object-fit:contain;display:block;margin:auto}article{background:white;padding:18px;margin:20px 0;border:1px solid #cbd1dc;border-radius:10px}h2{font-size:20px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd2db;text-align:left;padding:8px}</style><h1>克洛琳德 · 制作检查</h1><p>本轮角色已选定。当前为设计和母版／待机检查点，尚非25组完整动作交付。源图、拟合、播放、战斗逻辑、模拟器和真机分别验收。</p><p><a href="动作设计卡.md">25组设计卡</a> · <a href="制作与交付.md">制作记录</a> · <a href="checkpoint.json">文件与哈希</a></p><button onclick="document.body.classList.toggle('dark')">切换浅／深底</button>'''+cards+'''<h2>历史素材覆盖（仅文件核查）</h2><p>旧图初筛发现攻击缺少枪剑和游离残片；14组有候选不等于14组可交付，11组缺源图。</p><table><tr><th>动作</th><th>状态</th><th>原登记</th></tr>'''+rows+'''</table><h2>历史初筛证据</h2><img src="evidence/legacy-0.jpg"><img src="evidence/legacy-1.jpg"></html>'''
page=page.replace('<h1>克洛琳德 · 制作检查</h1>', '<h1>克洛琳德 · 制作检查</h1><article><h2>最新：新轻1体型返修</h2><p>新动作板与单人图存在身材差异，已保存新返修候选。</p><a href="body-review.html">查看返修前后与单人体型参照</a></article>')
page=page.replace('<h2>历史素材覆盖（仅文件核查）</h2>','<details><summary>历史核查记录（本轮暂缓）</summary><h2>历史素材覆盖（仅文件核查）</h2>').replace('</html>','</details></html>')
(O/'index.html').write_text(page,encoding='utf-8')
queue=O/'production-jobs.json'
if queue.exists():
 jobs=json.loads(queue.read_text(encoding='utf-8'))
 for job in jobs:
  job['status']='source_candidate_requires_review' if (O/f"source/{job['key']}-v1.png").exists() else 'queued_after_body_review'
 queue.write_text(json.dumps(jobs,ensure_ascii=False,indent=2),encoding='utf-8')
files={p.relative_to(O).as_posix():{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in O.rglob('*') if p.is_file() and p.name!='manifest.json'}
(O/'manifest.json').write_text(json.dumps({'files':files,'status':'checkpoint_not_full_delivery'},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'sources':len(sources),'fileHashes':len(files),'fullDelivery':False},ensure_ascii=False))
