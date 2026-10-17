"""Record and diagnose generated candidates. Does not claim game integration."""
from pathlib import Path
import json, hashlib, shutil, ast, base64, zipfile
from PIL import Image, ImageFilter, ImageDraw
import numpy as np
V=Path(__file__).resolve().parents[1]; R=V.parent
E=V/'evidence/full-delivery-20261009'; A=V/'assets/full-delivery-20261009'
A.mkdir(exist_ok=True); E.mkdir(exist_ok=True)
plan=json.loads((V/'design/FULL_PRODUCTION_JOBS_20261009.json').read_text())
jobs={j['id']:j for j in plan['jobs']}
# Reuse only pure color/rectangle diagnostic helpers; avoid legacy import side effects.
tree=ast.parse((V/'tools/fit_action_batch.py').read_text())
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name in ['lab','rects']:
        exec(compile(ast.Module(body=[node],type_ignores=[]),'diagnostic_helpers','exec'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def resolve_reference(p):
    # Historical receipts retain the original generation path; resolve after clone.
    tail=str(p).split('/V4/',1)[-1]
    candidate=V/tail
    return candidate if candidate.exists() else Path(p)
records=[]; payload={}
for receipt in sorted(E.glob('batch-*.json')):
    for event in json.loads(receipt.read_text()):
        j=dict(jobs[event['id']]); j['prompt']=event.get('prompt',j['prompt'])
        if event['status']!='generated':
            j.update(status='tool_error',error=event.get('error'));records.append(j);continue
        source=A/(j['id']+'.png')
        if not source.exists():shutil.copyfile(event['local_source'],source)
        out=E/j['id'];out.mkdir(exist_ok=True)
        prompt=V/'prompts/full-delivery-20261009'/(j['id']+'.txt');prompt.parent.mkdir(exist_ok=True);prompt.write_text(j['prompt']+'\n')
        im=Image.open(source).convert('RGBA'); cols,rows=j['grid'];w,h=im.size
        ref=json.loads((V/'evidence'/f"{j['character']}-idle-review/fit.json").read_text())
        palette=ref['palette'];target_h=ref['optimized_height'];pl=lab(palette[:-1])
        fixed_scale=target_h/(h/rows);panels=[];frames=[];counts=[];edges=[];cells=[]
        for n in range(j['visible_pose_count']):
            box=(n%cols*w//cols,n//cols*h//rows,(n%cols+1)*w//cols,(n//cols+1)*h//rows)
            c=im.crop(box);c.save(out/f'source-{n}.png');alpha=np.asarray(c)[:,:,3]
            ep=[int((alpha[0]>32).sum()),int((alpha[-1]>32).sum()),int((alpha[:,0]>32).sum()),int((alpha[:,-1]>32).sum())]
            if any(ep):edges.append(n+1)
            small=c.convert('RGBa').resize((round(c.width*fixed_scale),target_h),Image.Resampling.BOX).convert('RGBA')
            b=np.asarray(small);mask=b[:,:,3]>=128;dist=((lab(b[:,:,:3])[...,None,:]-pl[None,None,:,:])**2).sum(axis=3)
            idx=dist.argmin(axis=2).astype(np.int16);idx[~mask]=-1
            dil=np.asarray(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0;idx[dil&~mask]=len(palette)-1
            local=np.zeros((*idx.shape,4),dtype=np.uint8);valid=idx>=0;local[valid,:3]=np.asarray(palette,dtype=np.uint8)[idx[valid]];local[valid,3]=255
            ox=60-round(w/cols*.5*fixed_scale);oy=100-round(h/rows*.92*fixed_scale)
            canvas=Image.new('RGBA',(120,112));canvas.paste(Image.fromarray(local),(ox,oy));canvas.save(out/f'fit-{n}.png')
            aa=np.asarray(canvas);ci=np.full((112,120),-1,dtype=np.int16)
            for color_id,color in enumerate(palette):ci[np.all(aa[:,:,:3]==color,axis=2)&(aa[:,:,3]>0)]=color_id
            rr=rects(ci);reb=np.zeros_like(aa)
            for x,y,rw,rh,color_id in rr:reb[y:y+rh,x:x+rw]=[*palette[color_id],255]
            assert np.array_equal(reb,aa)
            counts.append(len(rr));frames.append({'index':n,'root_candidate':[60,100],'measured_anchors':False,'edge_pixels':ep,'rects':rr,'exact_reconstruction':True,'source_sha256':sha(out/f'source-{n}.png'),'fit_sha256':sha(out/f'fit-{n}.png')})
            panel=Image.new('RGB',(720,280))
            for col,img,bg in [(0,c,'#e5e8ec'),(1,canvas,'#222936'),(2,canvas,'#e5e8ec')]:
                p=Image.new('RGB',(240,280),bg);factor=min(225/img.width,250/img.height);tmp=img.resize((round(img.width*factor),round(img.height*factor)),Image.Resampling.LANCZOS if col==0 else Image.Resampling.NEAREST);p.paste(tmp,((240-tmp.width)//2,10),tmp);ImageDraw.Draw(p).text((8,265),['SOURCE','FIT DARK','FIT LIGHT'][col],fill='#888');panel.paste(p,(col*240,0))
            panels.append(panel);cells.append([base64.b64encode((out/f'source-{n}.png').read_bytes()).decode(),base64.b64encode((out/f'fit-{n}.png').read_bytes()).decode()])
        panels[0].save(out/'playback.gif',save_all=True,append_images=panels[1:],duration=160,loop=0)
        comparison=Image.new('RGB',(720,280*len(panels)))
        for n,p in enumerate(panels):comparison.paste(p,(0,n*280))
        comparison.save(out/'comparison.png')
        fit={'id':j['id'],'source_sha256':sha(source),'palette':palette,'fixed_scale':fixed_scale,'scale_scope':'nominal cells only; anatomical scale and true root require manual calibration','counts':counts,'source_edges':edges,'frames':frames,'method':'recorded shared palette / premult BOX / OKLab nearest / 1px outline / diagnostic scan-rect; NOT V3 painter','runtime':False,'accepted':False}
        (out/'fit.json').write_text(json.dumps(fit,ensure_ascii=False,indent=2)+'\n')
        j.update(output=str(source.relative_to(R)),sha256=sha(source),image_size=list(im.size),alpha_extrema=list(im.getchannel('A').getextrema()),status='needs_correction' if edges or max(counts)>760 else 'source_candidate_requires_visual_review',source_edges=edges,rect_counts=counts,prompt_file=str(prompt.relative_to(R)),fit_report=str((out/'fit.json').relative_to(R)),playback=str((out/'playback.gif').relative_to(R)),issues=['实际身体尺度/脚底/握点待校准','独立武器/助手/特效待补','没有运行时/模拟器/真机验收'])
        j['reference_hashes']=[{'path':str(resolve_reference(p).relative_to(R)),'sha256':sha(resolve_reference(p))} for p in j['refs']]
        records.append(j);payload[j['id']]={'frames':cells,'counts':counts,'edges':edges}
result={'scope':'original_hidden_14_all_25_groups','generated_sources':sum('output' in r for r in records),'generated_display_poses':sum(r['visible_pose_count'] for r in records if 'output' in r),'records':records,'game_integrated':0,'accepted':0,'quota_exhausted':False}
# Only a literal quota error may update this; transport/rate errors remain separate.
for r in records:
    if r.get('error') and any(word in r['error'].lower() for word in ['quota exceeded','quota exhausted','额度耗尽','image generation limit','image generation quota']):result['quota_exhausted']=True
(E/'ACTUAL_MANIFEST.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
queue=json.loads((V/'design/FULL_DELIVERY_QUEUE_20261009.json').read_text())
for r in records:
    if 'output' not in r:continue
    e=next(x for x in queue['entries'] if x['actionId']==r['character']+'.'+r['group'])
    e.update(new_source=r['output'],source_status=r['status'],runtime=False,simulator=False,device=False,accepted=False,complete=False,fitting={'report':r['fit_report'],'rect_counts':r['rect_counts'],'anchors_measured':False},playback=r['playback'])
queue['full_production_records']=records;queue['quota_exhausted']=result['quota_exhausted']
(V/'design/FULL_DELIVERY_CURRENT_20261009.json').write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n')
OUT=R.parent/'deliverables';OUT.mkdir(exist_ok=True)
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V4 全动作制作检查</title><style>body{font:16px system-ui;background:#202631;color:#eef;margin:20px}select,button{font:inherit;padding:10px;margin:4px}main{display:flex;gap:12px;flex-wrap:wrap}figure{margin:0;flex:1;min-width:280px}img{width:100%;height:55vh;object-fit:contain;background:#e5e8ec}#fit{background:#222936;image-rendering:pixelated}p{line-height:1.6}</style><select id="choice"></select><button id="prev">上一姿</button><button id="toggle">播放</button><button id="next">下一姿</button><p id="note"></p><main><figure><figcaption>源图</figcaption><img id="source"></figure><figure><figcaption>诊断拟合</figcaption><img id="fit"></figure></main><p>源图与诊断拟合候选。真实锚点、完整独立层和游戏接入尚未完成；正式验收0。</p><script>const DATA=__DATA__;const sel=document.getElementById('choice');let i=0,playing=false;for(const k of Object.keys(DATA)){let o=document.createElement('option');o.value=k;o.textContent=k;sel.append(o)}function draw(){const d=DATA[sel.value];i=(i+d.frames.length)%d.frames.length;document.getElementById('source').src='data:image/png;base64,'+d.frames[i][0];document.getElementById('fit').src='data:image/png;base64,'+d.frames[i][1];document.getElementById('note').textContent=sel.value+' · 姿势 '+(i+1)+'/'+d.frames.length+' · '+d.counts[i]+'图元 · 触边姿 '+d.edges.join(',')}sel.onchange=()=>{i=0;draw()};document.getElementById('toggle').onclick=()=>{playing=!playing};document.getElementById('prev').onclick=()=>{i--;draw()};document.getElementById('next').onclick=()=>{i++;draw()};setInterval(()=>{if(playing){i++;draw()}},180);draw();</script></html>'''.replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')))
(OUT/'V4_Full_Production_Preview.html').write_text(html)
with zipfile.ZipFile(OUT/'V4_Full_Production_Checkpoint.zip','w',zipfile.ZIP_DEFLATED) as z:
    for sub in ['assets/full-delivery-20261009','evidence/full-delivery-20261009','prompts/full-delivery-20261009','docs']:
        for p in (V/sub).rglob('*'):
            if p.is_file():z.write(p,str(p.relative_to(R)))
    for p in V.glob('design/FULL*20261009.json'):z.write(p,str(p.relative_to(R)))
    z.write(V/'tools/process_full_production.py','V4/tools/process_full_production.py')
    z.write(OUT/'V4_Full_Production_Preview.html','V4_Full_Production_Preview.html')
print(json.dumps({'generated_sources':result['generated_sources'],'display_poses':result['generated_display_poses'],'quota_exhausted':result['quota_exhausted'],'next_request':len(records)},ensure_ascii=False))
