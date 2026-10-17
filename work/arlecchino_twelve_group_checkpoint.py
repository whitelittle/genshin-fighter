from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
r=Path.cwd();o=r/'outputs/arlecchino-actions-20261011';d=json.loads((o/'actions.json').read_text(encoding='utf-8'));b=json.loads((o/'browser-twelve-groups.json').read_text(encoding='utf-8'));assert len(b['checks'])==116;assert all(x['ready'] for x in b['checks']);assert not b['consoleErrors']
checked=[]
for key,a in d.items():
 assert len(a['sourceFrames'])==len(a['frames'])==len(a['durations'])==len(a['phases'])
 for sf,ff in zip(a['sourceFrames'],a['frames']):
  raw=np.array(Image.open(o/sf['source']).convert('RGBA').crop(sf['roi']));im=np.array(Image.open(o/sf['file']).convert('RGBA'));m=im[:,:,3]>0;assert np.array_equal(im[m],raw[m]),sf['file']
  im=np.array(Image.open(o/ff['file']).convert('RGBA'));meta=json.loads((o/ff['rectData']).read_text(encoding='utf-8'));arr=np.zeros_like(im)
  for x,y,w,h,c in meta['rects']:arr[y:y+h,x:x+w]=meta['palette'][c]+[255]
  assert np.array_equal(arr,im),ff['file'];checked.append(ff['file'])
report={'actions':len(d),'displayPoses':len(checked),'sourceRGBAPreserved':'all retained pixels match original source ROI; reviewed background remnant excluded','pixelRoundtrip':'58 active fitted PNGs byte-for-byte reconstruction from rectangles','browser':'116 current source/fit pose states checked; no console error','peakBodyRectangles':max(f['rectangles'] for a in d.values() for f in a['frames']),'artAccepted':False,'runtimeIntegrated':False,'simulator':'not run','device':'not observed'}
(o/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
s=json.loads((o/'current-status.json').read_text(encoding='utf-8'));s['actionsWithNewPoses']=len(d);s['newDisplayPoses']=len(checked);s['pendingNewGroups']=[g['actionId'].split('.')[-1] for g in json.loads((o/'动作设计卡.json').read_text(encoding='utf-8'))['groups'] if g['actionId'].split('.')[-1] not in d];s['offlineChecks']=report['pixelRoundtrip'];s['browser']=report['browser'];s['sourceCandidatesReadyForExtraction']=[]
for name in ['crouchheavy-v1','airlight-v1','airheavy-v1']:
 p=o/'source'/f'{name}.png';im=Image.open(p).convert('RGBA');a=np.array(im)[:,:,3];s['sourceCandidatesReadyForExtraction'].append({'source':p.relative_to(o).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':list(im.size),'outerAlpha128':int((a[:,[0,-1]]>=128).sum()),'active':False,'status':'源候选已保存；待完整对象/杆轴提取、身体源单位与空中虚拟支撑/落地复核'})
s['nextStep']='继续已保存蹲重/空轻/空重提取，不重复生成；补E/Q、双人投技/被投、前后冲、倒地起身/胜败及独立特效；最终复核握点/武器长度/支撑/比例。';(o/'current-status.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
with (o/'制作与交付.md').open('a',encoding='utf-8') as f:f.write('''\n## 最新检查点：十二组58姿\n\n钩斩六姿、重攻六姿和蹲轻四姿已加入。重攻不再以刀尖最低点定脚底：逐姿鞋底支持Y保存于`source-calibration.json`；原有效姿刀尖低于脚底，源图返修v3又发生边缘接触，当前改用完整单图`heavy-effective-single-v4.png`，旧图保留。不同制图单位均为等比，不横压纵拉。\n\n提取进一步保留封闭主体内部较低alpha的衣料阴影，仍保持原RGBA；已识别的刀下独立背景残片以源坐标排除。世界尺度板给长柄武器预留较宽位置，避免板面邻图重叠造成多武器假象。\n\n58个实际活动拟合PNG用矩形逐像素重建一致；活动透明图所有保留RGBA与原图对应裁区一致；当前12组116源图/拟合浏览器逐姿状态载入通过、未见控制台错误。活动身体连持武器峰值1558矩形，未得出双人平台池/真机负载合格结论。截图`evidence/heavy-ground-repair-v4.jpg`，非正式模拟器。\n\n仍缺13组、独立特效、统一Q演出与双人挂点；全套人体单位、武器握点/长度、循环衔接及正式战斗/模拟器/真机未验收。已经生成并保存蹲重/空轻/空重三组源候选及提示词，尚未提取/接入，不计完成。继续`current-status.json`。\n''')
for p in [r/'AI_START.md',r/'docs/current/V4_执行与验收台账_20261009.md']:
 with p.open('a',encoding='utf-8') as f:f.write('\n> 2026-10-11 阿蕾奇诺最新：12组58姿候选，补钩斩/重攻/蹲轻并修重攻穿地与源图边缘；58矩形重建和116当前源图/拟合逐姿检查通过。峰值1558，不等于平台预算/真机通过。仍缺13组及特效/Q/双人配对，蹲重/空轻/空重源图已保存待处理；最终比例/握点/循环待验收。继续`outputs/arlecchino-actions-20261011/current-status.json`。\n')
manifest={'candidate':True,'sourceTool':'built-in image_gen','actions':len(d),'poses':len(checked),'files':[]}
for p in sorted(o.rglob('*')):
 if p.is_file() and p.name!='manifest.json':manifest['files'].append({'path':p.relative_to(o).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(o/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
