"""Two targeted source repairs, shared-palette fitting and inline-friendly art playback."""
from pathlib import Path
import json,copy,hashlib,re
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from build_zhongli_delivery import fit
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/zhongli-design-20261011';OLD=OUT/'batches/20261011-resume';B=OUT/'batches/20261011-refinement'
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def marks(coords):return dict(zip(['skull','chin','neck','pelvis','root','leftHip','leftKnee','leftAnkle','rightHip','rightKnee','rightAnkle'],coords))
def stage(p,mode='optimized',size=(800,420),dark=False):
 bg=Image.new('RGB',size,'#242c38' if dark else '#dce2e9');d=ImageDraw.Draw(bg);anchor=[size[0]//2,size[1]-35];d.line([(0,anchor[1]),(size[0],anchor[1])],fill='#8291a1')
 item=dict(file=p['source'],root=p['landmarks']['root'],displayScale=p['scale']) if mode=='source' else p[mode]
 im=Image.open(B/item['file']).convert('RGBA');factor=item['displayScale'];im=im.resize((max(1,round(im.width*factor)),max(1,round(im.height*factor))),Image.Resampling.NEAREST if mode!='source' else Image.Resampling.LANCZOS);bg.paste(im,(round(anchor[0]-item['root'][0]*factor),round(anchor[1]-item['root'][1]*factor)),im);return bg

def main():
 prior=json.loads((OLD/'report.json').read_text());palette=prior['palette'];new=[]
 specs=[('walk-padding','walk-padding-v3.png',[[881,85],[916,220],[881,232],[865,557],[642,1065],[835,575],[696,861],[582,1018],[895,565],[1010,834],[1102,999]]),('light1-recovery','light1-recovery-v2.png',[[715,130],[745,250],[680,265],[645,550],[333,1073],[620,556],[435,803],[326,1002],[685,552],[794,803],[842,1000]])]
 for key,file,coords in specs:
  im=Image.open(B/file).convert('RGBA');lm=marks(coords);scale=(114*330/920)/(lm['chin'][1]-lm['skull'][1]);a=np.array(im);y,x=np.where(a[:,:,3]>=128)
  p=dict(id=key,source=file,sourceSHA256=sha(B/file),sourceSize=list(im.size),landmarks=lm,scale=scale,accepted=False,registration='人工初步标点，透视与腿链尚未验收',opaqueMargins=[int(x.min()),int(y.min()),int(im.width-1-x.max()),int(im.height-1-y.max())],transparentFraction=float((a[:,:,3]==0).mean()),torsoDeviation=float(np.linalg.norm(np.array(lm['pelvis'])-lm['neck'])*scale/(262*330/920)-1))
  p['torsoReviewFlag']=abs(p['torsoDeviation'])>.08
  p['legSegmentsStage']={side:[float(np.linalg.norm(np.array(lm[side+a])-lm[side+c])*scale) for a,c in [('Hip','Knee'),('Knee','Ankle')]] for side in ['left','right']}
  for mode,opt in [('initial',False),('optimized',True)]:
   f,rects=fit(im,scale,palette,opt);name=f'{key}-{mode}.png';f.save(B/name);p[mode]=dict(file=name,root=[v*scale/4 for v in lm['root']],displayScale=4,rectangles=len(rects));write(B/f'{key}-{mode}-rects.json',dict(palette=palette,size=list(f.size),rects=rects,root=p[mode]['root'],sourceSHA256=p['sourceSHA256'],fittedSHA256=sha(B/name),previewOnly=True))
  new.append(p)
 light=[]
 for original in prior['poses'][3:8]:
  p=copy.deepcopy(original);p['source']='../20261011-resume/'+p['source']
  for mode in ['initial','optimized']:p[mode]['file']='../20261011-resume/'+p[mode]['file']
  light.append(p)
 light.append(copy.deepcopy(new[1]));end=copy.deepcopy(light[0]);end['id']='light1-ready-return';light.append(end)
 durations=[3,3,2,2,5,6,8];phases=['持枪准备','转身蓄势','前刺接触','伸展随挥','撤枪','回收过渡候选','复用持枪准备姿']
 report=dict(palette=palette,poses=light,newSources=new,state='候选，不接正式战斗',sourceCommit='1c21eb57ffb1b8d88b41cbb743c46a34864849df',notes=['行走右边距1→220像素，完整两鞋；没有满足提示词所要求的四边10%留白，最小边距30像素。','恢复源图无邻姿金色残片；第二稿顶部边距92像素；首稿4像素并躯干投影冲突，保留历史。两脚高差、腿链与动作连续性待复核。','原第6姿提取图顶部存在邻姿残片，本候选撤出该帧，改用新回收候选；原图保留。','末姿精确复用持枪准备姿，完成候选序列的闭合；并未解决空手母姿到持枪的转换。','背身蓄势到前刺的转向、腿链、握点和枪长尚未验收。','同一既有21色板，premultiplied BOX、棕黑内侧一格保护亮部、painter精确还原。'],browserQA='未执行',simulator='未执行',device='未执行')
 write(B/'report.json',report)
 action=dict(actionId='zhongli_light1_refinement_candidate',tickRate=60,durations=durations,phases=phases,frames=light,combatDesign=dict(startup=6,active=4,recovery=sum(durations)-10,events=[dict(tick=6,kind='hit-candidate',hitId='zhongli_light1_candidate_1',damageSegments=1)],status='design-only; no runtime hitboxes'),state='art-only candidate',issues=report['notes'])
 write(B/'light1-action-candidate.json',action)
 html=(OLD/'light1-action-review.html').read_text();html=re.sub(r'(<script type="application/json" id="data">).*?(</script>)',lambda m:m[1]+json.dumps(dict(report=report,action=action),ensure_ascii=False).replace('<','\\u003c')+m[2],html,flags=re.S)
 html=html.replace("while(i<5&&t>=boundaries[i+1])","while(i<poses.length-1&&t>=boundaries[i+1])").replace('(i+6)%6','(i+poses.length)%poses.length').replace("min=\"0\" max=\"20\"","min=\"0\" max=\"28\"").replace("'/20 · 第'","'/28 · 第'").replace('恢复11tick','恢复19tick').replace('复用已有六姿返修图；','复用已有五姿，新增回收候选，末姿复用持枪准备；').replace('href="review.html"','href="../../制作检查.html"')
 html=html.replace('<section><h2>剩余问题</h2>','<section><h2>直接查看慢放</h2><img style="max-width:100%" src="light1-slow.gif" alt="轻攻一拟合候选四倍慢放"><p>四倍慢放；关节与连续性未验收。</p></section><section><h2>剩余问题</h2>')
 (B/'light1-action-review.html').write_text(html)
 frames=[stage(p) for p in light];frames[0].save(B/'light1-slow.gif',save_all=True,append_images=frames[1:],duration=[round(v*1000/60/10)*40 for v in durations],loop=0,disposal=2)
 # Before/after at independently registered, uniform anatomical scales.
 oldwalk=copy.deepcopy(prior['poses'][2]);oldwalk['source']='../20261011-resume/'+oldwalk['source']
 for mode in ['initial','optimized']:oldwalk[mode]['file']='../20261011-resume/'+oldwalk[mode]['file']
 panels=[(oldwalk,'source','Old walk: right margin 1px'),(new[0],'source','Walk repair: right margin 220px'),(new[0],'optimized','Shared palette / optimized'),(new[1],'source','New recovery candidate'),(new[1],'optimized','Recovery / optimized'),(end,'optimized','Return: reused armed ready')]
 board=Image.new('RGB',(2400,900),'#f3f5f8');d=ImageDraw.Draw(board)
 for i,(p,mode,label) in enumerate(panels):
  im=stage(p,mode,size=(800,420));board.paste(im,(i%3*800,i//3*450+30));d.text((i%3*800+12,i//3*450+8),label,fill='#243249')
 board.save(B/'comparison.png');write(B/'批次记录.json',dict(newGenerated=3,reusedAttackSources=5,endFrameExactlyReusesReady=True,oldSixthFrame='保留历史，邻姿残片而撤出此候选',verification='原图边距和拟合重建已查；美术／浏览器／正式逻辑／真机未验收',files=['walk-padding-v3.png','light1-recovery-v1.png','light1-recovery-v2.png','comparison.png','light1-slow.gif'],prompts='prompts.json'))
 print(json.dumps(dict(newSources=[dict(id=p['id'],margins=p['opaqueMargins'],rects=p['optimized']['rectangles'],torsoDeviation=p['torsoDeviation']) for p in new],frames=len(light)),ensure_ascii=False))
if __name__=='__main__':main()
