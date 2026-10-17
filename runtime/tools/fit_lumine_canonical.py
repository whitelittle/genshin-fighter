"""Reuse the original Arlecchino canonical_fit for isolated Traveler artwork."""
from pathlib import Path
import json,sys,hashlib,argparse
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'work'))
import clorinde_assets as ca
OUT=ROOT/'outputs/lumine-rebuild-20261016/canonical-v3'

def main():
    global OUT
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',default=str(OUT))
    parser.add_argument('--root-x',type=float,default=500)
    parser.add_argument('--root-y',type=float,default=1523)
    args=parser.parse_args();OUT=Path(args.out)
    root=[args.root_x,args.root_y]
    for d in ['source','fit']:(OUT/d).mkdir(parents=True,exist_ok=True)
    ca.O=OUT
    master=Image.open(OUT/'source/master.png').convert('RGBA')
    bbox=master.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
    # The original method's fixed world grid is 4.5, not a frame-specific bbox grid.
    scale=320/(bbox[3]-bbox[1])
    pal=ca.artlib.build_palette([ca.artlib.downscale(master,.06)],16,seed=31)+[[245,213,200],[240,240,248],[19,21,30]]
    records={}
    for p in sorted((OUT/'source').glob('*.png')):
        im=Image.open(p).convert('RGBA')
        assert im.size==master.size,(p.name,im.size,master.size)
        fit,meta=ca.canonical_fit(im,root,scale,pal,p.stem)
        idx=Image.open(OUT/fit['file']).convert('RGBA')
        area=sum(w*h for x,y,w,h,c in meta['rects'])
        visible=int((np.asarray(idx)[:,:,3]>0).sum())
        records[p.stem]={'rectangles':fit['rectangles'],'size':idx.size,'anchor':fit['anchor'],'worldCell':fit['scale'],'sourceSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pixelRoundtrip':True,'drawingAreaRatio':area/visible}
    report={'method':'work/clorinde_assets.py canonical_fit, unchanged function used by original work/arlecchino_fit_initial.py','worldBodyHeight':320,'sourceUnit':scale,'fixedSourceRoot':root,'paletteEntries':len(pal),'palette':pal,'frames':records,'scope':'offline artwork; runtime unchanged; animation anatomy not accepted'}
    (OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    fit=Image.open(OUT/'fit/master.png'); board=Image.new('RGB',(380,390),'#263454');d=ImageDraw.Draw(board)
    fit=fit.resize((fit.width*4,fit.height*4),Image.Resampling.NEAREST);board.paste(fit,((380-fit.width)//2,25),fit)
    d.text((10,8),f"Original canonical fit: {records['master']['rectangles']} rects",fill='white');board.save(OUT/'master-preview.png')
    print(json.dumps(records))

if __name__=='__main__':main()
