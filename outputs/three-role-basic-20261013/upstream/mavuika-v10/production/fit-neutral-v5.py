"""Retain source RGBA; encode fixed-grid candidates without per-pose recentering."""
from pathlib import Path
import json, hashlib, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent/'tools'))
import artlib
root=Path(__file__).resolve().parents[1]; assets=root/'dist/assets'
specs={'idle':(2,1,.24),'walk':(3,2,.408),'backwalk':(3,2,.408)}
cells={}; groups={}; report=[]
for key,(cols,rows,scale) in specs.items():
    path=assets/f'mavuika-{key}-source-v5.png'; im=Image.open(path).convert('RGBA')
    w,h=im.size; cw,ch=w//cols,h//rows; alpha=np.array(im)[:,:,3]
    groups[key]={'source':path.name,'sourceSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'columns':cols,'rows':rows,'cellSize':[cw,ch],'displayScale':scale,'sourceAnchor':[cw/2,ch*.965],'poses':[],'alphaZeroFraction':float((alpha==0).mean())}
    for i in range(cols*rows):
        x,y=(i%cols)*cw,(i//cols)*ch
        crop=im.crop((x,y,x+cw,y+ch)); small=artlib.downscale(crop,scale/4)
        cells[key,i]=small
        mask=np.array(crop)[:,:,3]>32; yy,xx=np.where(mask)
        bbox=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
        groups[key]['poses'].append({'sourceRect':[x,y,cw,ch],'sourceBBox':bbox,'footBaselineDeltaPx':round((bbox[3]-ch*.965)*scale,2),'anchor':[cw*scale/8,ch*.965*scale/4],'atlasRect':[(i%cols)*64,(i//cols)*64,small.width,small.height]})
palette=artlib.build_palette(list(cells.values()),20,seed=11)+[[43,25,27]]
for key,(cols,rows,scale) in specs.items():
    for mode in ['initial','optimized']:
        atlas=Image.new('RGBA',(cols*64,rows*64)); rectData=[]
        for i,p in enumerate(groups[key]['poses']):
            im=cells[key,i]; idx=artlib.apply_palette(im,palette)
            if mode=='optimized':
                mask=idx>=0; edge=mask&~ndimage.binary_erosion(mask,np.ones((3,3)),border_value=0)
                a=np.array(im); bright=(a[:,:,:3].max(2)>210)&(a[:,:,:3].min(2)>130)
                idx[edge&~bright]=len(palette)-1
            rects=artlib.painter(idx); restored=np.full(idx.shape,-1,dtype=int)
            for x,y,w,h,c in rects:restored[y:y+h,x:x+w]=c
            assert np.array_equal(restored,idx),f'{key}/{i}/{mode} reconstruction mismatch'
            encoded=artlib.render(rects,palette,im.width,im.height)
            assert im.width<=64 and im.height<=64
            atlas.paste(encoded,tuple(p['atlasRect'][:2]))
            rectData.append({'pose':i,'width':im.width,'height':im.height,'rects':rects,'anchor':p['anchor'],'scale':4})
            p[mode+'Rectangles']=len(rects)
            report.append({'group':key,'pose':i,'mode':mode,'rectangles':len(rects)})
        file=f'mavuika-{key}-{mode}-v5.png'; atlas.save(assets/file); groups[key][mode]=file
        (assets/f'{key}-{mode}-rects-v5.json').write_text(json.dumps({'palette':palette,'poses':rectData,'sourceSHA256':groups[key]['sourceSHA256'],'status':'candidate; anchor and gait acceptance pending'},separators=(',',':'))+'\n')
data={'groups':groups,'palette':palette,'status':'14 candidate display poses; not 25-group character completion','anchorPolicy':'fixed cell-center X and fixed per-sheet floor Y; no per-pose bounding-box recentering','issues':['Source support-contact and pelvis drift remain visible; fixed anchors are provisional.','Forward/backward cycle half-stride parity needs revision, not accepted as finished six-pose gait.','No formal combat, simulator, device or user acceptance.']}
(assets/'neutral-rig-v5.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(root/'production/neutral-fit-report-v5.json').write_text(json.dumps({'pipeline':'premultiplied BOX / weighted OKLab shared 20+outline palette / painter exact reconstruction','records':report,'optimizedMax':max(r['rectangles'] for r in report if r['mode']=='optimized'),'optimizedMean':round(np.mean([r['rectangles'] for r in report if r['mode']=='optimized']),2),'scope':'offline encoding verification only'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'poses':len(cells),'reconstructions':len(report),'optimizedMax':max(r['rectangles'] for r in report if r['mode']=='optimized'),'alpha':{k:v['alphaZeroFraction'] for k,v in groups.items()}},ensure_ascii=False))
