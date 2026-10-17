from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
r=Path.cwd();o=r/'outputs/arlecchino-actions-20261011';d=json.loads((o/'actions.json').read_text(encoding='utf-8'));checked=[]
for key,a in d.items():
 assert len(a['frames'])==len(a['sourceFrames'])==len(a['durations'])==len(a['phases']);assert all(x>0 for x in a['durations'])
 for sf,ff in zip(a['sourceFrames'],a['frames']):
  raw=np.array(Image.open(o/sf['source']).convert('RGBA').crop(sf['roi']));obj=np.array(Image.open(o/sf['file']).convert('RGBA'));visible=obj[:,:,3]>0;assert raw.shape==obj.shape;assert np.array_equal(raw[visible],obj[visible]),sf['file']
  meta=json.loads((o/ff['rectData']).read_text(encoding='utf-8'));im=np.array(Image.open(o/ff['file']).convert('RGBA'));rebuilt=np.zeros_like(im)
  for x,y,w,h,c in meta['rects']:rebuilt[y:y+h,x:x+w]=meta['palette'][c]+[255]
  assert np.array_equal(im,rebuilt),ff['file'];checked.append(ff['file'])
bs=[]
for file,count in [('browser-five-groups.json',48),('browser-base-four.json',36)]:
 b=json.loads((o/file).read_text(encoding='utf-8'));assert len(b['checks'])==count;assert all(s['ready'] for s in b['checks']);assert not b['consoleErrors'];bs.extend(b['checks'])
for s in bs:
 if s['selected']=='jump' and s['phase'] in [0,1,5]:assert abs(s['root'][1]-550)<.001
report={'actions':len(d),'displayPoses':len(checked),'sourceRGBAPreserved':True,'pixelRoundtrip':'42 actual fitted PNGs reconstructed byte-for-byte from rectangles','browser':'48 existing pose-mode checks plus 36 new pose-mode checks; no console errors; grounded jump phases root verified','artAccepted':False,'runtimeIntegrated':False,'simulator':'not run','device':'not observed','peakBodyRectangles':max(f['rectangles'] for a in d.values() for f in a['frames'])}
(o/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
s=json.loads((o/'current-status.json').read_text(encoding='utf-8'));s['actionsWithNewPoses']=len(d);s['newDisplayPoses']=len(checked);s['pendingNewGroups']=[g['actionId'].split('.')[-1] for g in json.loads((o/'动作设计卡.json').read_text(encoding='utf-8'))['groups'] if g['actionId'].split('.')[-1] not in d];s['repairs']=['walk left/right support identity and cycle','idle support registration and loop seam','held weapon geometry/grip/length and thin source-alpha edges','all new body units remain final visual candidates'];s['offlineChecks']=report['pixelRoundtrip'];s['browser']=report['browser'];s['newSourceTrialsNotActive']={'light2-v1':'wrong butt-first thrust instead of blade sweep','heavy-v1':'effective-stage scythe choreography wrong; redraw required','light3-v1':'needs separate hook/weapon transition review'};s['nextStep']='finish hook and heavy with blade-first single-pose references; then crouch/air attacks, E/Q, dash, paired throws and shared directional fall/wakeup/victory/defeat';(o/'current-status.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
note='''\n## 最新检查点：九组42姿\n\n已修轻1第三姿弯曲杆轴、重画前走经过姿，补镰刃在前的轻2六姿及蹲下/站防/蹲防各四姿、跳跃六姿。当前9/25组42显示姿候选，其余16组仍未补齐。轻2首版与重攻首版误画成枪尾刺，明确不进入当前动作表；轻3首版仍需钩斩和武器翻转复核，不计已接入新组。\n\n薄枪杆alpha低于衣装主体；仅用alpha250会使镰刃与握持手分离。已用目视源坐标的杆轴支持区域保留原RGBA，未绘制替代直线。离线逐图比对42个透明图的所有有效RGBA与对应原图裁区一致；42个拟合PNG实际用矩形逐像素重建一致。9组单身体连持武器峰值1430矩形，不据此宣称双人池或真机通过。\n\n浏览器已有五组48源图/拟合逐姿检查，新增四组36次，均无控制台错误。跳跃空中姿使用虚拟支撑，世界轨迹6tick起跳、34tick进入落地，预蹲/蹬地/落地根坐标实际检查为550；这是播放器演出，不是正式物理或确定性模拟器。截图见`evidence/light2-player-v2.jpg`、`evidence/jump-player-v1.jpg`，当前世界尺度板见`evidence/world-current-*.jpg`。\n\n武器握点/长度、左右支撑身份、待机循环和新组体型仍待最终美术复核；不是9组最终验收。原源图、失败试图、提示词和旧拟合都保留。当前重建脚本`work/arlecchino_fit_initial.py`会重建九组；播放器现行源文件直接保留，不再运行早期UI壳脚本。\n'''
with (o/'制作与交付.md').open('a',encoding='utf-8') as f:f.write(note)
for p in [r/'AI_START.md',r/'docs/current/V4_执行与验收台账_20261009.md']:
 with p.open('a',encoding='utf-8') as f:f.write('\n> 2026-10-11 阿蕾奇诺最新：9组42姿新候选，轻1杆轴与前走经过姿返修、轻2镰刃前向、蹲下/双防/跳跃已保存；原RGBA保留、42拟合矩形重建及48+36浏览器逐姿检查通过。仍缺16组，重攻/轻3试图未采用或待复核，最终体型/握点/支撑及正式战斗/模拟器/真机未通过。继续`outputs/arlecchino-actions-20261011/current-status.json`，不制作其他角色。\n')
manifest={'candidate':True,'sourceTool':'built-in image_gen','actions':len(d),'poses':len(checked),'files':[]}
for f in sorted(o.rglob('*')):
 if f.is_file() and f.name!='manifest.json':manifest['files'].append({'path':f.relative_to(o).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(o/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
