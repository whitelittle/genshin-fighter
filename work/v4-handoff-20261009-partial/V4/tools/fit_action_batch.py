"""Offline diagnostic; NOT a replacement for V3 artlib/painter or runtime."""
from pathlib import Path
from PIL import Image,ImageFilter,ImageDraw
import numpy as np,json,hashlib,base64
V=Path(__file__).resolve().parents[1];R=V.parent;P=V/'design/ACTION_QUEUE_20261009.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lab(rgb):
 a=np.asarray(rgb,dtype=float)/255;a=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
 lms=a@np.array([[.4122214708,.2119034982,.0883024619],[.5363325363,.6806995451,.2817188376],[.0514459929,.1073969566,.6299787005]])
 return np.cbrt(lms)@np.array([[.2104542553,1.9779984951,.0259040371],[.7936177850,-2.4285922050,.7827717662],[-.0040720468,.4505937099,-.8086757660]])
def rects(idx):
 rr=[];active={}
 for y,row in enumerate(idx):
  cur={};x=0
  while x<len(row):
   c=int(row[x]);end=x+1
   while end<len(row) and int(row[end])==c:end+=1
   if c>=0:
    key=(x,end-x,c)
    if key in active:rect=active[key];rect[3]+=1
    else:rect=[x,y,end-x,1,c];rr.append(rect)
    cur[key]=rect
   x=end
  active=cur
 return rr
jobs=json.loads(P.read_text());payload={};summary=[];outroot=V/'evidence/actions-20261009';outroot.mkdir(exist_ok=True)
for s in jobs['generation_specs']:
 if not s.get('output'):continue
 key=s['character'];g=s['group'];source=R/s['output'];im=Image.open(source).convert('RGBA');assert sha(source)==s['sha256']
 cols,rows=s['grid'];w,h=im.size;ref=json.loads((V/'evidence'/f'{key}-idle-review/fit.json').read_text());pal=ref['palette'];height=ref['optimized_height'];pl=lab(pal[:-1]);d=outroot/s['id'];d.mkdir(exist_ok=True);frames=[];pairs=[];counts=[];cells=[]
 for n in range(cols*rows):
  box=(n%cols*w//cols,n//cols*h//rows,(n%cols+1)*w//cols,(n//cols+1)*h//rows);c=im.crop(box);c.save(d/f'source-cell-{n}.png');a=np.asarray(c)[:,:,3];edges={'top':bool((a[0]>32).any()),'bottom':bool((a[-1]>32).any()),'left':bool((a[:,0]>32).any()),'right':bool((a[:,-1]>32).any())}
  scale=height/(h/rows);small=c.convert('RGBa').resize((round(c.width*scale),height),Image.Resampling.BOX).convert('RGBA');b=np.asarray(small);mask=b[:,:,3]>=128;dist=((lab(b[:,:,:3])[...,None,:]-pl[None,None,:,:])**2).sum(axis=3);idx=dist.argmin(axis=2).astype(np.int16);idx[~mask]=-1
  dil=np.asarray(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0;idx[dil&~mask]=len(pal)-1
  local=np.zeros((*idx.shape,4),dtype=np.uint8);valid=idx>=0;local[valid,:3]=np.asarray(pal,dtype=np.uint8)[idx[valid]];local[valid,3]=255
  # Nominal cell-root transform is fixed, never recenter to changing silhouette.
  ox=50-round((w/cols*.5)*scale);oy=92-round((h/rows*.92)*scale);canvas=Image.new('RGBA',(100,104));canvas.paste(Image.fromarray(local),(ox,oy));canvas.save(d/f'optimized-{n}.png')
  aa=np.asarray(canvas);ci=np.full((104,100),-1,dtype=np.int16)
  for j,color in enumerate(pal):ci[np.all(aa[:,:,:3]==color,axis=2)&(aa[:,:,3]>0)]=j
  rr=rects(ci);reb=np.zeros_like(aa)
  for x,y,rw,rh,j in rr:reb[y:y+rh,x:x+rw]=[*pal[j],255]
  assert np.array_equal(reb,aa),'exact rectangle reconstruction'
  counts.append(len(rr));frames.append({'source_cell_sha256':sha(d/f'source-cell-{n}.png'),'fit_sha256':sha(d/f'optimized-{n}.png'),'source_edge_alpha32':edges,'rects':rr,'reconstruction_exact':True,'root_candidate':[50,92],'anchors_measured':False})
  pair=Image.new('RGB',(720,320));
  for col,image,bg in [(0,c,'#dfdbce'),(1,canvas,'#222936'),(2,canvas,'#dfdbce')]:
   panel=Image.new('RGB',(240,320),bg);factor=min(230/image.width,292/image.height);tmp=image.resize((round(image.width*factor),round(image.height*factor)),Image.Resampling.NEAREST if col else Image.Resampling.LANCZOS);panel.paste(tmp,((240-tmp.width)//2,12),tmp);ImageDraw.Draw(panel).text((8,304),['SOURCE','FIT / DARK','FIT / LIGHT'][col],fill='#888888');pair.paste(panel,(240*col,0))
  pairs.append(pair);cells.append([base64.b64encode((d/f'source-cell-{n}.png').read_bytes()).decode(),base64.b64encode((d/f'optimized-{n}.png').read_bytes()).decode()])
 pairs[0].save(d/'playback.gif',save_all=True,append_images=pairs[1:],duration=120 if g in ['walk','backwalk'] else ([160,110,160,220]*((len(pairs)+3)//4))[:len(pairs)],loop=0);sheet=Image.new('RGB',(720,320*len(pairs)))
 for n,x in enumerate(pairs):sheet.paste(x,(0,320*n))
 sheet.save(d/'comparison.png');report={'id':s['id'],'character':key,'group':g,'source':s['output'],'source_sha256':s['sha256'],'palette':pal,'palette_sha256':ref['palette_sha256'],'palette_scope':'reuse current recorded character idle/walk palette; whole-action recalibration pending','fixed_scale':scale,'root':[50,92],'anchors_measured':False,'method':'premultiplied-alpha BOX; recorded palette nearest OKLab; 1px outline; diagnostic scan-run rectangle merge, NOT recovered V3 painter','rect_counts':counts,'max_rects':max(counts),'within_historical_760':max(counts)<=760,'frames':frames,'runtime_integrated':False,'device_tested':False,'accepted':False};(d/'fit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));s['fitting']={'report':str((d/'fit.json').relative_to(R)),'frames':len(frames),'rect_counts':counts,'source_edges':[n+1 for n,f in enumerate(frames) if any(f['source_edge_alpha32'].values())],'status':'diagnostic_candidate','anchors_measured':False}
 for group in s.get('action_groups',[g]):
  indices=s.get('group_pose_indices',{}).get(group,list(range(len(frames))));entry=next(x for x in jobs['entries'] if x['actionId']==key+'.'+group);entry['fitting']=dict(s['fitting'],source_pose_indices=indices,rect_counts=[counts[n] for n in indices]);selected=[pairs[n] for n in indices];play=d/f'{group}-playback.gif';selected[0].save(play,save_all=True,append_images=selected[1:],duration=120 if group in ['walk','backwalk'] else ([160,110,160,220]*((len(selected)+3)//4))[:len(selected)],loop=0);entry['playback']=str(play.relative_to(R));item={'id':key+'.'+group,'rect_counts':[counts[n] for n in indices],'source_edges':[n+1 for n in indices if any(frames[n]['source_edge_alpha32'].values())],'accepted':False};payload[key+'.'+group]={'frames':[cells[n] for n in indices],'summary':item}
 summary.append({'id':s['id'],'rect_counts':counts,'source_edges':s['fitting']['source_edges'],'accepted':False});print(s['id'],counts,'source edges',s['fitting']['source_edges'],flush=True)
(outroot/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));P.write_text(json.dumps(jobs,ensure_ascii=False,indent=2)+'\n')
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>V4跨角色动作候选</title><style>body{font:16px system-ui;background:#202631;color:#eef;padding:24px}select,button{padding:10px;margin:5px}img{max-width:46%;height:68vh;object-fit:contain;background:#ddd9ce}#fit{image-rendering:pixelated;background:#222936}p{line-height:1.7}</style><h1>V4 跨角色动作候选</h1><p>源图／离线诊断拟合。未接入武器、助手、特效、判定或客户端。火神walk-v3带光晕且步态不合格，保留待修。</p><select id="choice"></select><button id="toggle">暂停</button><button id="prev">上一姿</button><button id="next">下一姿</button><p id="note"></p><img id="source"><img id="fit"><script>const DATA=__DATA__;const sel=document.getElementById('choice');let i=0,playing=true;for(const k of Object.keys(DATA)){let o=document.createElement('option');o.value=k;o.textContent=k;sel.append(o)}function draw(){const d=DATA[sel.value];i=(i+d.frames.length)%d.frames.length;document.getElementById('source').src='data:image/png;base64,'+d.frames[i][0];document.getElementById('fit').src='data:image/png;base64,'+d.frames[i][1];document.getElementById('note').textContent=sel.value+' · 姿势'+(i+1)+'/'+d.frames.length+' · '+d.summary.rect_counts[i]+'图元 · 源格触边姿 '+d.summary.source_edges.join(',')+' · 正式验收0'}sel.onchange=()=>{i=0;draw()};document.getElementById('toggle').onclick=()=>{playing=!playing};document.getElementById('prev').onclick=()=>{i--;draw()};document.getElementById('next').onclick=()=>{i++;draw()};setInterval(()=>{if(playing){i++;draw()}},220);draw();</script></html>'''.replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')))
(R/'V4_All_Characters_Action_Preview.html').write_text(html)
