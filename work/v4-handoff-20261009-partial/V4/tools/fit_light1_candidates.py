from pathlib import Path
import sys,json,hashlib,base64,io
import numpy as np
from PIL import Image,ImageFilter
V=Path(__file__).resolve().parents[1];sys.path.insert(0,str(V.parent/'game/tools'));import artlib
summary=[];payload={}
jobs=json.loads((V/'design/ROSTER_JOBS.json').read_text())['jobs']
for source in [V.parent/j['light1_body_candidate']['output'] for j in jobs if 'light1_body_candidate' in j]:
 key=source.name.split('-light1-body')[0]
 if key=='mavuika' and source.name.endswith('v1.png'):continue
 if key=='mavuika' and not source.name.endswith('v2.png'):continue
 d=V/'evidence'/f'{key}-light1-review';d.mkdir(exist_ok=True)
 im=Image.open(source).convert('RGBA');w,h=im.size;order=[0,1,2,3];cells=[im.crop(((n%2)*w//2,(n//2)*h//2,(n%2+1)*w//2,(n//2+1)*h//2)) for n in order]
 ref=json.loads((V/'evidence'/f'{key}-idle-review'/'fit.json').read_text());pal=ref['palette'];height=ref['optimized_height'];counts=[];data=[];seq=[];records=[]
 for i,c in enumerate(cells):
  c.save(d/f'source-cell-{i}.png');small=artlib.downscale(c,height/c.height);idx=artlib.apply_palette(small,pal[:-1]);mask=Image.fromarray((idx>=0).astype('uint8')*255);dil=np.asarray(mask.filter(ImageFilter.MaxFilter(3)))>0;idx[dil&(idx<0)]=len(pal)-1
  rr=artlib.painter(idx);a=np.zeros((*idx.shape,4),dtype='uint8');m=idx>=0;a[m,:3]=np.asarray(pal,dtype='uint8')[idx[m]];a[m,3]=255
  reconstructed=np.zeros_like(a)
  for x,y,rw,rh,ci in rr:reconstructed[y:y+rh,x:x+rw]=[*pal[ci],255]
  assert np.array_equal(a,reconstructed),'rects must reconstruct fitted pixels exactly'
  out=Image.fromarray(a);out.save(d/f'optimized-{i}.png');counts.append(len(rr));records.append({'source_grid_index':order[i],'rects':rr,'source_cell_sha256':hashlib.sha256((d/f'source-cell-{i}.png').read_bytes()).hexdigest(),'fit_sha256':hashlib.sha256((d/f'optimized-{i}.png').read_bytes()).hexdigest(),'foot_anchor':None,'leftGrip':None,'rightGrip':None,'rect_reconstruction_exact':True})
  pair=Image.new('RGB',(640,260));
  for col,img,bg in [(0,c,'#dedbd0'),(1,out,'#232936')]:
   scale=min(300/img.width,230/img.height);tmp=img.resize((round(img.width*scale),round(img.height*scale)),Image.Resampling.NEAREST if col else Image.Resampling.LANCZOS);frame=Image.new('RGB',(320,260),bg);frame.paste(tmp,((320-tmp.width)//2,10),tmp);pair.paste(frame,(col*320,0))
  seq.append(pair)
  data.append([base64.b64encode((d/f'source-cell-{i}.png').read_bytes()).decode(),base64.b64encode((d/f'optimized-{i}.png').read_bytes()).decode()])
 seq[0].save(d/'playback.gif',save_all=True,append_images=seq[1:],duration=[200,160,200,250],loop=0)
 sheet=Image.new('RGB',(640,1040));
 for i,f in enumerate(seq):sheet.paste(f,(0,i*260))
 sheet.save(d/'source-fit-comparison.png')
 report={'character':key,'group':'light1','source':str(source.relative_to(V.parent)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'palette':pal,'palette_sha256':ref['palette_sha256'],'palette_scope':'复用该角色待机/步态共享调色板；本轮未重校全动作','height':height,'rect_counts':counts,'max_rects':max(counts),'budget760':max(counts)<=760,'grid_order':order,'anchor_status':'未测脚底/手掌；按原格展示，不逐帧裁切居中','frames':records,'status':'offline_candidate_not_runtime_or_device','issues':['独立道具/助手/特效缺失','手型/衣料/体型一致性待更正','预算不通过时保留原尺度，不缩小掩盖复杂度']}
 (d/'fit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));summary.append({k:report[k] for k in ['character','grid_order','rect_counts','max_rects','budget760','status']});payload[key]={'frames':data,'report':summary[-1]};print(key,counts,flush=True)
(V/'evidence/light1-fit-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>V4 轻攻1身体候选播放</title><style>body{background:#202631;color:#eef;font:16px system-ui;padding:24px}select,button{padding:10px;margin:6px}img{width:45%;height:65vh;object-fit:contain;image-rendering:pixelated;background:#dedbd0}#fit{background:#282f3a}p{line-height:1.7}</style><h1>V4 轻攻1身体候选播放</h1><p>仅源图与拟合身体。未接入武器、助手、特效或碰撞；格底不是已标定脚底。保持同角色待机调色板与尺度，超预算明确保留。</p><select id="char"></select><button id="play">暂停</button><button id="prev">上一姿</button><button id="next">下一姿</button><p id="note"></p><img id="source"><img id="fit"><script>const DATA=__DATA__;const source=document.getElementById('source'),fit=document.getElementById('fit'),note=document.getElementById('note');const sel=document.getElementById('char');for(const k of Object.keys(DATA)){let o=document.createElement('option');o.value=k;o.textContent=k;sel.append(o)}let i=0,playing=true;function draw(){const d=DATA[sel.value];i=(i+4)%4;source.src='data:image/png;base64,'+d.frames[i][0];fit.src='data:image/png;base64,'+d.frames[i][1];note.textContent=sel.value+' · '+(i+1)+'/4 · '+d.report.rect_counts[i]+'图元 · 单帧760目标'+(d.report.budget760?'以内':'超出，待优化')+' · 源格顺序 '+d.report.grid_order.join(',')}sel.onchange=()=>{i=0;draw()};document.getElementById('play').onclick=()=>{playing=!playing;document.getElementById('play').textContent=playing?'暂停':'播放'};document.getElementById('prev').onclick=()=>{i--;draw()};document.getElementById('next').onclick=()=>{i++;draw()};setInterval(()=>{if(playing){i++;draw()}},240);draw();</script></html>'''.replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')))
(V.parent.parent/'V4_Light1_Candidate_Preview.html').write_text(html)
print('Validated',len(summary)*4,'fitted frames via exact rectangle reconstruction')
