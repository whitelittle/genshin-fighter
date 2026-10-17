from pathlib import Path
import json,hashlib
p=Path('outputs/arlecchino-actions-20261011');b=json.loads((p/'browser-initial.json').read_text(encoding='utf-8'));assert len(b['checks'])==16;assert all(s['ready'] for s in b['checks']);assert all(s['frames']==2 for s in b['checks'][:4]);assert all(s['frames']==6 for s in b['checks'][4:]);print('16 pose-mode browser states checked')
v=json.loads((p/'fitting-verification.json').read_text(encoding='utf-8'));v['browser']='16 pose-mode states inspected; source/fit, timeline, mirror control, white background; no console error';(p/'fitting-verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
with (p/'制作与交付.md').open('a',encoding='utf-8') as f:f.write('\n## 最新制作检查点：两组八姿\n\n母版按alpha250主体加两源像素边缘提取，保留主体RGBA与源坐标，padding保护发梢；不是重画身体或横纵变形，原背景失败图保留。见`mother-extraction.json`及浅深底证据。待机采用两张新绘制呼吸/眨眼候选，前走采用六张新姿势。全部源画布无主体裁边，统一19色拟合与矩形像素重建通过，单身体峰值899矩形，非真机负载结论。\n\n原展示页UI下，源图/拟合16次逐姿检查、时间轴、镜像控制与白底载入通过，控制台未见错误。独立浏览器不是正式模拟器。当前仅2/25组候选；步态第六姿没有充分表现经过支撑脚、待机两姿的脚底/衣尾微差与循环衔接仍需精校，不能称最终动作验收通过。其他23组、攻击/特效、Q/双方投技与正式逻辑仍待完成。\n\n接续：优先返修步态经过姿与支撑接触、核对待机脚底，再制作枪尾短击代表招与后退；不要把缺少的23组替换成待机。播放器`player.html`，服务仅指向此目录，端口8770；需要重启时使用本地http.server。重建依次运行`arlecchino_extract_mother.py`、`arlecchino_fit_initial.py`、`arlecchino_world_board.py`，播放器当前源文件保留。\n')
manifest={'candidate':True,'sourceTool':'built-in image_gen','actions':2,'poses':8,'files':[]}
for f in sorted(p.rglob('*')):
 if f.is_file() and f.name!='manifest.json':manifest['files'].append({'path':f.relative_to(p).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(p/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
