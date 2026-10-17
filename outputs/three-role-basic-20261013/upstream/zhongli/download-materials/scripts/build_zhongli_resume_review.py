"""Rebuild recovered art candidates, preserving original PNGs and provisional landmarks."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy import ndimage
from PIL import Image
from build_zhongli_delivery import fit,artlib
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'outputs/zhongli-design-20261011/batches/20261011-resume'
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 rows=[]
 for key,file,marks in [('idle-0','mother-clean-candidate.png',[[704,78],[750,244],[713,260],[722,642],[566,1398]]),('idle-1','idle-second-candidate.png',[[727,78],[780,250],[735,265],[738,640],[574,1440]]),('walk-0','walk-first-candidate.png',[[852,60],[889,221],[836,244],[866,600],[530,1232]])]:
  rows.append(dict(id=key,source=file,image=Image.open(B/file).convert('RGBA'),landmarks=dict(zip(['skull','chin','neck','pelvis','root'],marks)),roi=None))
 sheet=Image.open(B/'light1-existing-repair.png').convert('RGBA');a=np.asarray(sheet);labels,n=ndimage.label(a[:,:,3]>=64);sizes=np.bincount(labels.ravel());ids=sorted(range(1,n+1),key=lambda i:sizes[i],reverse=True)[:6];assert len(ids)==6 and min(sizes[i] for i in ids)>3000
 pieces=[]
 for ident in ids:
  y,x=np.where(labels==ident);roi=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)];crop=np.array(sheet.crop(roi));crop[:,:,3]=np.where(labels[roi[1]:roi[3],roi[0]:roi[2]]==ident,crop[:,:,3],0);pieces.append((float(np.median(y)),float(np.median(x)),roi,Image.fromarray(crop)))
 pieces.sort(key=lambda p:(int(p[0]//(sheet.height/3)),p[1]))
 marks=[[[335,31],[355,92],[337,104],[327,247],[443,461]],[[925,33],[946,94],[930,101],[950,250],[1081,465]],[[275,515],[293,563],[280,579],[276,683],[439,850]],[[949,511],[970,562],[951,575],[946,680],[1100,845]],[[340,892],[361,947],[343,959],[341,1068],[493,1228]],[[942,850],[962,910],[944,923],[960,1048],[1113,1238]]]
 for i,(_,_,roi,im) in enumerate(pieces):
  name=f'light1-{i}-source.png';im.save(B/name);rows.append(dict(id=f'light1-{i}',source=name,image=im,roi=roi,sheet='light1-existing-repair.png',landmarks={k:[x-roi[0],y-roi[1]] for k,(x,y) in zip(['skull','chin','neck','pelvis','root'],marks[i])}))
 head_target=114*330/920;torso_target=262*330/920
 for row in rows:
  lm=row['landmarks'];row['scale']=330/(lm['root'][1]-lm['skull'][1]) if row['id'].startswith('idle') else head_target/(lm['chin'][1]-lm['skull'][1])
 palette=artlib.build_palette([artlib.downscale(r['image'],r['scale']/4) for r in rows],20,seed=11)+[[40,29,27]]
 poses=[]
 for row in rows:
  im=row.pop('image');scale=row['scale'];lm=row['landmarks'];arr=np.array(im);y,x=np.where(arr[:,:,3]>=128);row['sourceSize']=list(im.size);row['sourceSHA256']=sha(B/row['source']);row['opaqueMargins']=[int(x.min()),int(y.min()),int(im.width-1-x.max()),int(im.height-1-y.max())];row['accepted']=False;row['registration']='manual provisional; hip/knee/ankle not yet registered';row['rootKind']='support';row['headStageLength']=float(np.linalg.norm(np.array(lm['chin'])-lm['skull'])*scale);row['torsoStageLength']=float(np.linalg.norm(np.array(lm['pelvis'])-lm['neck'])*scale);row['torsoDeviation']=row['torsoStageLength']/torso_target-1;row['torsoReviewFlag']=abs(row['torsoDeviation'])>.08
  for mode,opt in [('initial',False),('optimized',True)]:
   image,rects=fit(im,scale,palette,opt);name=f'{row["id"]}-{mode}.png';image.save(B/name);row[mode]=dict(file=name,root=[v*scale/4 for v in lm['root']],displayScale=4,rectangles=len(rects));write(B/f'{row["id"]}-{mode}-rects.json',dict(palette=palette,size=list(image.size),rects=rects,root=row[mode]['root'],sourceSHA256=row['sourceSHA256'],fittedSHA256=sha(B/name),previewOnly=True))
  poses.append(row)
 # Explicit joint registrations are manual estimates, not automatic anatomy detection.
 joints=[[[681,648],[615,1000],[562,1350],[753,652],[749,1000],[770,1320]],[[694,652],[627,1023],[571,1396],[772,653],[770,1030],[797,1374]],[[826,617],[696,871],[592,1168],[891,623],[1068,900],[1140,1167]],[[296,249],[234,350],[174,437],[343,250],[400,357],[434,426]],[[924,250],[842,360],[756,432],[971,250],[1038,360],[1075,430]],[[250,690],[177,763],[66,826],[305,687],[370,745],[418,818]],[[919,688],[820,761],[719,820],[972,686],[1055,734],[1095,815]],[[315,1070],[221,1145],[113,1208],[365,1068],[454,1135],[489,1200]],[[935,1048],[864,1141],[774,1210],[982,1050],[1047,1130],[1056,1208]]]
 for p,coords in zip(poses,joints):
  offset=p['roi'][:2] if p['roi'] else [0,0]
  p['landmarks'].update({k:[x-offset[0],y-offset[1]] for k,(x,y) in zip(['leftHip','leftKnee','leftAnkle','rightHip','rightKnee','rightAnkle'],coords)})
  p['legSegmentsStage']={side:[float(np.linalg.norm(np.array(p['landmarks'][side+a])-p['landmarks'][side+b])*p['scale']) for a,b in [('Hip','Knee'),('Knee','Ankle')]] for side in ['left','right']}
  p['registration']='manual provisional skull/chin/neck/pelvis/hip/knee/ankle/support; not accepted'
 report=dict(state='恢复后候选复核；不是正式动作验收',sourceCommit='1c21eb57ffb1b8d88b41cbb743c46a34864849df',pipeline='artlib premultiplied BOX, weighted OKLab shared palette, exact painter reconstruction',palette=palette,poses=poses,notes=['旧母版外部仍有棕色晕染，已保存去晕染候选；身份细节和比例仍需复核。','行走修复稿右鞋只有1像素边距，补边返修又切掉左侧头发和衣尾；两稿均未采用。','轻攻一复用已有六姿返修图，没有重复绘制。','躯干偏差仅用于筛查；透视和手工标点都可能影响结果。','腿链、完整播放、模拟器、真机均未验收。'],rectangles=dict(max=max(p['optimized']['rectangles'] for p in poses),mean=sum(p['optimized']['rectangles'] for p in poses)/len(poses)),browserQA='未执行，当前环境不提供受支持的浏览器检查')
 write(B/'report.json',report)
 prompts=[dict(id='mother',file='mother-clean-candidate.png',instruction='保留钟离原图的身份、轮廓、服装和姿势，仅去除人物外部棕灰晕染；真透明背景，无阴影、闪光、粗描边；全身保留边距。'),dict(id='idle',file='idle-second-candidate.png',instruction='以去晕染母版为身份参考，微呼吸第二姿；脚位、脚底线、头颈腿长、服装不变，仅胸肩和手肘微动；无缩放、裁切、晕染和阴影。'),dict(id='walk',file='walk-first-candidate.png',instruction='参考原行走图与母版，仅修复缺失右鞋尖并扩展右侧透明画布；保留走路姿势、身体和腿长，去外部晕染，不缩小人物。'),dict(id='margin',file='walk-margin-rejected.png',instruction='右侧扩展约15%透明边距，角色姿势、比例、颜色不变，不重新居中，不裁切；单姿。',result='返修失败：左侧头发和衣尾被裁切，拒绝采用')]
 write(B/'prompts.json',dict(provenance='从本轮对话恢复的指令摘要；不是原始工具请求逐字日志',prompts=prompts))
 page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>钟离 · 恢复批次动作复核</title><style>body{font:16px/1.65 system-ui;max-width:1400px;margin:auto;padding:24px;background:#f2f4f7;color:#263249}nav{display:flex;gap:16px;flex-wrap:wrap}button,a{cursor:pointer}section{background:white;padding:18px;margin:20px 0;border-radius:8px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}canvas{width:100%;height:auto;background:#e5e8eb;image-rendering:pixelated}.dark canvas{background:#232b36}.notice{background:#fff0d1;padding:14px}.meta{font-size:14px}.frame{overflow-x:auto}@media(max-width:850px){.grid{grid-template-columns:1fr}}</style><h1>钟离 · 待机／行走／轻攻一候选复核</h1><p class="notice">9姿同一调色板：原图、初始拟合、优化拟合并排。标点为人工初步登记；全部未验收。旧母版曾残留晕染，已纠正记录；行走两次修复尚未满足边距要求。</p><nav><a href="../../制作检查.html">历史库存与母版</a><a href="report.json" download>下载拟合台账</a><a href="prompts.json" download>下载恢复的指令摘要</a><button id="theme">深浅背景</button><button id="play">播放待机候选</button></nav><section><h2>待机两姿播放</h2><canvas id="loop" width="800" height="420"></canvas><p>脚底锚点对齐仅为检查；不能将当前循环登记为脚位已通过。</p></section><main id="cards"></main><script>
const images=new Map();let report,playing=false,index=0;const modes=['source','initial','optimized'];
function draw(canvas,p,mode){const c=canvas.getContext('2d');c.clearRect(0,0,800,420);c.imageSmoothingEnabled=false;const item=mode==='source'?{file:p.source,root:p.landmarks.root,displayScale:p.scale}:p[mode];const im=images.get(item.file);c.strokeStyle='#8290a0';c.beginPath();c.moveTo(0,385);c.lineTo(800,385);c.stroke();if(im)c.drawImage(im,400-item.root[0]*item.displayScale,385-item.root[1]*item.displayScale,im.width*item.displayScale,im.height*item.displayScale);}
async function start(){report=JSON.parse(document.querySelector('#data').textContent);const files=new Set(report.poses.flatMap(p=>[p.source,p.initial.file,p.optimized.file]));await Promise.all([...files].map(async f=>{const im=new Image();im.src=f;await im.decode();images.set(f,im);}));for(const p of report.poses){const s=document.createElement('section');const h=document.createElement('h2');h.textContent=p.id;s.append(h);const g=document.createElement('div');g.className='grid';for(const mode of modes){const d=document.createElement('div'),label=document.createElement('p'),canvas=document.createElement('canvas');label.textContent={source:'原图',initial:'初始拟合',optimized:'优化拟合'}[mode];canvas.width=800;canvas.height=420;d.append(label,canvas);g.append(d);draw(canvas,p,mode);}s.append(g);const meta=document.createElement('p');meta.className='meta';meta.textContent='边距 左/上/右/下：'+p.opaqueMargins.join('/')+'；优化图元 '+p.optimized.rectangles+'；躯干偏差 '+(p.torsoDeviation*100).toFixed(1)+'%'+(p.torsoReviewFlag?'，需复核':'')+'；未验收';s.append(meta);document.querySelector('#cards').append(s);}draw(document.querySelector('#loop'),report.poses[0],'optimized');}
document.querySelector('#theme').onclick=()=>document.body.classList.toggle('dark');document.querySelector('#play').onclick=()=>{playing=!playing;document.querySelector('#play').textContent=playing?'暂停':'播放待机候选';};setInterval(()=>{if(playing&&report){index=1-index;draw(document.querySelector('#loop'),report.poses[index],'optimized');}},400);start().catch(e=>document.querySelector('#cards').textContent='载入失败：'+e.message);
</script></html>'''
 page=page.replace('<script>', '<script type="application/json" id="data">'+json.dumps(report,ensure_ascii=False).replace('<','\\u003c')+'</script><script>',1)
 (B/'review.html').write_text(page,encoding='utf-8')
 print(json.dumps(dict(poses=len(poses),rectangles=report['rectangles'],flags=[p['id'] for p in poses if p['torsoReviewFlag']]),ensure_ascii=False))
if __name__=='__main__':main()
