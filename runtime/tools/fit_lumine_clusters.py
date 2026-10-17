"""Offline cluster-art candidates; does not replace live character data."""
from pathlib import Path
import json, sys, hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'game/tools'))
import artlib as A

def main():
    out=ROOT/'outputs/lumine-rebuild-20261016/cluster-v2'
    source=out/'source';fit=out/'fit'; fit.mkdir(exist_ok=True)
    master=Image.open(source/'master.png').convert('RGBA')
    box=master.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox()
    factor=72/(box[3]-box[1])
    raw={};meta={}
    for path in sorted(source.glob('*.png')):
        im=Image.open(path).convert('RGBA');bbox=im.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox()
        raw[path.stem]=A.downscale(im.crop(bbox),factor)
        meta[path.stem]={'bbox':bbox,'sourceSha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    palette=A.build_palette(list(raw.values()),16,seed=21)
    for key,im in raw.items():
        idx=A.despeckle(A.apply_palette(im,palette));rects=A.painter(idx)
        target=A.render(rects,palette,im.width,im.height)
        expected=np.zeros((im.height,im.width,4),dtype=np.uint8)
        for i,c in enumerate(palette):expected[idx==i]=c+[255]
        assert np.array_equal(np.asarray(target),expected)
        target.save(fit/f'{key}.png')
        meta[key].update(size=im.size,rectangles=len(rects))
    report={'scope':'offline candidate; anatomy and aesthetics not accepted; no runtime changes','factor':factor,'masterHeight':72,'palette':palette,'frames':meta}
    (out/'fit-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    canvas=Image.new('RGB',(660,350),'#263454');d=ImageDraw.Draw(canvas)
    for i,(path,label) in enumerate([(ROOT/'outputs/lumine-rebuild-20261016/fit/idle_0.png','Previous rejected'),(fit/'master.png','New cluster candidate'),(ROOT/'outputs/lumine-rebuild-20261016/sampling-audit/nahida-runtime-lo-idle.png','Nahida / style only')]):
        im=Image.open(path);im=im.resize((round(im.width*260/im.height),260),Image.Resampling.NEAREST)
        canvas.paste(im,(220*i+(220-im.width)//2,45),im);d.text((220*i+10,16),label,fill='white')
    canvas.save(out/'master-comparison.png')
    print(json.dumps({k:{'size':v['size'],'rectangles':v['rectangles']} for k,v in meta.items()}))

if __name__=='__main__': main()
