from pathlib import Path
import sys,json,hashlib,base64,io,re
import numpy as np
from PIL import Image
V=Path(__file__).resolve().parents[1];sys.path.insert(0,str(V.parent/'game/tools'));import artlib
records=[];payload={}
def encode(im):
 f=io.BytesIO();im.save(f,format='PNG');return base64.b64encode(f.getvalue()).decode()
queue=json.loads((V/'design/ROSTER_JOBS.json').read_text())
for job in sorted(queue['jobs'],key=lambda j:j['character']):
 src=V.parent/job['E_effect_candidate']['output']
 key=src.name.split('-E-fx')[0];d=V/'evidence'/f'{key}-E-fx-review';d.mkdir(exist_ok=True);im=Image.open(src).convert('RGBA');w,h=im.size;cells=[im.crop(((n%2)*w//2,(n//2)*h//2,(n%2+1)*w//2,(n//2+1)*h//2)) for n in range(4)]
 small=[artlib.downscale(c,80/c.height) for c in cells];rgbpal=artlib.build_palette(small,16);pal=[[*c,a] for a in [64,128,255] for c in rgbpal]
 def fit_cells(height):
  result=[]
  for c in cells:
   im=artlib.downscale(c,height/c.height);idx=artlib.apply_palette(im,rgbpal,alpha_cut=32);alpha=np.asarray(im)[:,:,3];idx[idx>=0]+=np.where(alpha[idx>=0]<=85,0,np.where(alpha[idx>=0]<=170,1,2))*len(rgbpal);rr=artlib.painter(idx);a=np.zeros((*idx.shape,4),dtype='uint8');m=idx>=0;a[m]=np.asarray(pal,dtype='uint8')[idx[m]];result.append((Image.fromarray(a),rr))
  return result
 initial=fit_cells(80);height=80;optimized=initial
 while max(len(rr) for _,rr in optimized)>850 and height>32:
  height-=4;optimized=fit_cells(height)
 frames=[];seq=[];pics=[]
 for n,(c,im) in enumerate(zip(cells,[artlib.downscale(c,height/c.height) for c in cells])):
  c.save(d/f'source-cell-{n}.png');idx=artlib.apply_palette(im,rgbpal,alpha_cut=32);alpha=np.asarray(im)[:,:,3];idx[idx>=0]+=np.where(alpha[idx>=0]<=85,0,np.where(alpha[idx>=0]<=170,1,2))*len(rgbpal)
  rr=artlib.painter(idx);arr=np.zeros((*idx.shape,4),dtype='uint8');mask=idx>=0;arr[mask]=np.asarray(pal,dtype='uint8')[idx[mask]];rebuilt=np.zeros_like(arr)
  for x,y,rw,rh,ci in rr:rebuilt[y:y+rh,x:x+rw]=pal[ci]
  assert np.array_equal(arr,rebuilt)
  initial[n][0].save(d/f'initial-{n}.png');fit=Image.fromarray(arr);fit.save(d/f'optimized-{n}.png');a=np.asarray(c)[:,:,3];edge=bool((a[0,:]>=32).any() or (a[-1,:]>=32).any() or (a[:,0]>=32).any() or (a[:,-1]>=32).any())
  frames.append({'rects':rr,'rect_count':len(rr),'source_edge_contact_alpha32':edge,'rect_reconstruction_exact':True,'source_cell_sha256':hashlib.sha256((d/f'source-cell-{n}.png').read_bytes()).hexdigest(),'fit_sha256':hashlib.sha256((d/f'optimized-{n}.png').read_bytes()).hexdigest(),'origin_measured':False})
  pair=Image.new('RGBA',(640,240),'#242936');
  for col,img in enumerate([c,fit]):
   t=img.resize((round(img.width*220/img.height),220),Image.Resampling.LANCZOS if col==0 else Image.Resampling.NEAREST);pair.alpha_composite(t,((320-t.width)//2+col*320,10))
  seq.append(pair.convert('RGB'));thumb=c.copy();thumb.thumbnail((360,240));pics.append([encode(thumb),encode(fit)])
 seq[0].save(d/'playback.gif',save_all=True,append_images=seq[1:],duration=[200,160,200,250],loop=0);sheet=Image.new('RGB',(640,960));
 for n,p in enumerate(seq):sheet.paste(p,(0,n*240))
 sheet.save(d/'source-fit-comparison.png');counts=[f['rect_count'] for f in frames];r={'character':key,'layer':'E_effect','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'palette':pal,'palette_scope':'本独立E特效4姿共享；身体palette另层','alpha_method':'premult BOX + weighted OKLab RGB16 + alpha buckets64/128/255; alpha<32 transparent','height':height,'initial_height':80,'initial_counts':[len(rr) for _,rr in initial],'rect_counts':counts,'max_rects':max(counts),'legacy850_reference':max(counts)<=850,'origin_status':'未标定，不等于身体接触/世界落点','status':'offline_effect_candidate','frames':frames};(d/'fit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));records.append({k:r[k] for k in ['character','rect_counts','max_rects','legacy850_reference','status']});payload[key]={'frames':pics,'counts':counts,'edge':[f['source_edge_contact_alpha32'] for f in frames]};print(key,counts,'edge',payload[key]['edge'],flush=True)
(V/'evidence/E-effect-fit-summary.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
body={}
for d in sorted((V/'evidence').glob('*-E-review')):
 key=d.name[:-9];r=json.loads((d/'fit.json').read_text());frames=[]
 for n in range(4):
  im=Image.open(d/f'source-cell-{n}.png');im.thumbnail((360,240));frames.append([encode(im),base64.b64encode((d/f'optimized-{n}.png').read_bytes()).decode()])
 body[key]={'frames':frames,'counts':r['rect_counts'],'edge':[False]*4}
DATA={'body':body,'effect':payload}
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V4 E身体与独立特效候选</title><style>body{background:#202631;color:#eef;font:16px system-ui;margin:0;padding:20px}select,button{padding:10px;margin:5px}img{width:47%;height:60vh;object-fit:contain;image-rendering:pixelated;background:#dedbd0}#fit{background:#282f3a}p{line-height:1.7}@media(max-width:600px){img{width:100%;height:40vh}}</style><h1>V4 E身体与独立特效候选</h1><p>14人 · 身体与特效分别浏览。武器/助手未补齐，尚未合成或接入判定。四姿播放速度仅预览，不等于60Hz逻辑tick。源图栏为缩图，完整源图与提示词在检查点中。</p><select id="char"></select><select id="layer"><option value="body">身体</option><option value="effect">独立特效</option></select><button id="play">暂停</button><button id="prev">上一姿</button><button id="next">下一姿</button><select id="bg"><option value="dark">深色</option><option value="light">浅色</option></select><p id="note"></p><img id="source"><img id="fit"><script>const DATA=__DATA__;const source=document.getElementById('source'),fit=document.getElementById('fit'),note=document.getElementById('note');const sel=document.getElementById('char');for(const k of Object.keys(DATA.body)){let o=document.createElement('option');o.value=k;o.textContent=k;sel.append(o)}let i=0,playing=true;function draw(){const mode=document.getElementById('layer').value,d=DATA[mode][sel.value];i=(i+4)%4;source.src='data:image/png;base64,'+d.frames[i][0];fit.src='data:image/png;base64,'+d.frames[i][1];const color=document.getElementById('bg').value==='dark'?'#282f3a':'#dedbd0';source.style.background=fit.style.background=color;note.textContent=sel.value+' · '+mode+' · '+(i+1)+'/4 · '+d.counts[i]+'图元 · 锚点未测'+(d.edge[i]?' · 源格边缘接触，疑似裁切需更正':'')+(sel.value==='yaemiko'&&mode==='effect'&&i===0?' · v2花瓣修正候选':'')+(sel.value==='clorinde'&&mode==='effect'&&i===2?' · v2方向修正候选':'')}sel.onchange=()=>{i=0;draw()};document.getElementById('layer').onchange=()=>{i=0;draw()};document.getElementById('bg').onchange=draw;document.getElementById('play').onclick=()=>{playing=!playing;document.getElementById('play').textContent=playing?'暂停':'播放'};document.getElementById('prev').onclick=()=>{i--;draw()};document.getElementById('next').onclick=()=>{i++;draw()};setInterval(()=>{if(playing){i++;draw()}},240);draw();</script></html>'''.replace('__DATA__',json.dumps(DATA,ensure_ascii=False,separators=(',',':')))
(V.parent.parent/'V4_E_Candidate_Preview.html').write_text(html)
print('56 effect frames exact pixel reconstruction; preview saved')
