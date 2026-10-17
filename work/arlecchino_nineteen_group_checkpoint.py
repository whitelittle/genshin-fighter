from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
r=Path.cwd();o=r/'outputs/arlecchino-actions-20261011';d=json.loads((o/'actions.json').read_text(encoding='utf-8'));b=json.loads((o/'browser-nineteen-groups.json').read_text(encoding='utf-8'));assert len(b['checks'])==200;assert all(s['ready'] for s in b['checks']);assert not b['consoleErrors']
for t in b['transitions']:
 assert t['after']['airRootSource']=='jump-current-root';assert all(abs(a-z)<1e-6 for a,z in zip(t['before']['root'],t['after']['root']));assert abs(t['landing']['root'][1]-550)<1e-6;assert abs(t['idle']['root'][1]-550)<1e-6
for key in ['forwarddash','backdash','victory']:
 for field in ['sourceFrames','frames']:assert d[key][field][0]==d['idle'][field][0]==d[key][field][-1]
for field in ['sourceFrames','frames']:
 assert d['airlight'][field][4]==d['jump'][field][4];assert d['airlight'][field][5]==d['jump'][field][5];assert d['airlight'][field][-1]==d['idle'][field][0];assert d['airheavy'][field][-1]==d['idle'][field][0]
checked=set()
for key,a in d.items():
 assert len(a['sourceFrames'])==len(a['frames'])==len(a['durations'])==len(a['phases'])
 for sf,ff in zip(a['sourceFrames'],a['frames']):
  raw=np.array(Image.open(o/sf['source']).convert('RGBA').crop(sf['roi']));im=np.array(Image.open(o/sf['file']).convert('RGBA'));m=im[:,:,3]>0;assert np.array_equal(im[m],raw[m]),sf['file']
  im=np.array(Image.open(o/ff['file']).convert('RGBA'));meta=json.loads((o/ff['rectData']).read_text(encoding='utf-8'));arr=np.zeros_like(im)
  for x,y,w,h,c in meta['rects']:arr[y:y+h,x:x+w]=meta['palette'][c]+[255]
  assert np.array_equal(arr,im),ff['file'];checked.add(ff['file'])
report={'actions':len(d),'displayStates':sum(len(a['frames']) for a in d.values()),'uniqueActiveFitSprites':len(checked),'sourceRGBAPreserved':True,'pixelRoundtrip':'all actual active fit PNGs reconstructed byte-for-byte from rectangles','browserStates':200,'jumpToAirRootTransitions':4,'sharedBookendsAndLanding':'passed','peakActiveBodyRectangles':max(f['rectangles'] for a in d.values() for f in a['frames']),'artAccepted':False,'runtimeIntegrated':False,'simulator':'not run','device':'not observed'}
(o/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');s=json.loads((o/'current-status.json').read_text(encoding='utf-8'));s['actionsWithNewPoses']=len(d);s['newDisplayPoses']=report['displayStates'];s['pendingNewGroups']=[g['actionId'].split('.')[-1] for g in json.loads((o/'动作设计卡.json').read_text(encoding='utf-8'))['groups'] if g['actionId'].split('.')[-1] not in d];s['offlineChecks']=report['pixelRoundtrip'];s['browser']='200 current source/fit pose states plus four jump->air root/landing transitions passed';s['sourceCandidatesReadyForExtraction']=[]
for name in ['E-v1','Q-body-v1']:
 p=o/'source'/f'{name}.png';im=Image.open(p).convert('RGBA');a=np.array(im)[:,:,3];s['sourceCandidatesReadyForExtraction'].append({'source':p.relative_to(o).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':list(im.size),'outerOpaqueEdge':int((a[[0,-1],:]>=128).sum()+(a[:,[0,-1]]>=128).sum()),'active':False,'status':'six body source candidates, no baked FX; not fitted or cinematic yet'})
s['nextStep']='继续E/Q已保存六姿提取并实现统一Q命中/短分支与独立特效；补投技/低位变体/被投、单向倒地与共享起身；完成25组后全套复核与交付。';s['airPhysicsBoundary']='Independent preview inherits current jump root position only; actual battle velocity/collision/interrupt inheritance not verified';(o/'current-status.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
with (o/'制作与交付.md').open('a',encoding='utf-8') as f:f.write('''\n## 最新检查点：十九组100显示状态\n\n已补蹲重、空轻/空重、前冲/后撤、胜利/败北。当前19/25组100显示状态、90个活动拟合图；空轻的下降/落地和两种空攻末姿、冲刺/胜利首尾复用真实已有姿，不伪称100张独立新图。\n\n提取归属改用不可变身体核心边界，解决蹲轻枪尾误归邻姿的源组件问题。按母版和世界尺度板复核部分显示单位（全程等比，不按剪影等高或为预算缩小）；自动肤色区跨度只作筛查，不能把红色镰刃/肤色连通区误判成真实头部尺寸。跳跃空中锚点保留175世界单位的虚拟支撑长度，空攻分别使用对应虚拟支撑，下降/落地独立；无源图身体变形。\n\n200次当前源图/拟合逐姿浏览器载入与四次跳跃顶点→空攻根坐标继承/落地/回待机检查通过；空攻首次root与原跳跃root相等，落地与恢复root Y=550。仅独立播放器演出，不代表正式速度/碰撞/中断继承通过。前后冲位移与源姿变化分离，首尾共用待机；胜利72tick、败北48tick。\n\n所有活动透明图保留RGBA与原图裁区一致，90个活动拟合PNG实际用矩形重建逐像素一致。活动身体峰值1448矩形；尚未计正式对手/全部特效并发，不登记平台池或真机合格。截图`evidence/airheavy-player-v1.jpg`，完整记录`browser-nineteen-groups.json`。\n\n尚缺E/Q、投技/被投、受击倒地/起身六组和独立特效；E/Q六姿源候选与提示词已保存，不计已接入或完整演出。下一步按`current-status.json`继续，不另选新角色。最终源比例、武器握点/形态/长度、循环/双人接触、正式游戏/模拟器/真机仍分别待验收。\n''')
for p in [r/'AI_START.md',r/'docs/current/V4_执行与验收台账_20261009.md']:
 with p.open('a',encoding='utf-8') as f:f.write('\n> 2026-10-11 阿蕾奇诺最新：19组100显示状态/90活动拟合图已保存；200当前源图/拟合逐姿与四次跳跃→空攻root继承/落地检查通过，独立播放非正式物理。修蹲轻枪尾归属并复核部分源单位，峰值1448未等同平台预算。尚缺E/Q、投技/被投、倒地/起身六组及特效，E/Q源图已保存待提取；继续`outputs/arlecchino-actions-20261011/current-status.json`，不制作其他新角色。\n')
manifest={'candidate':True,'sourceTool':'built-in image_gen','actions':len(d),'displayStates':report['displayStates'],'uniqueActiveFitSprites':len(checked),'files':[]}
for p in sorted(o.rglob('*')):
 if p.is_file() and p.name!='manifest.json':manifest['files'].append({'path':p.relative_to(o).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(o/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
