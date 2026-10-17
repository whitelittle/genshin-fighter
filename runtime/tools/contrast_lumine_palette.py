"""Offline color-table candidate; preserve source geometry, sampling and rects."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'game/tools'))
from artlib import render
OUT=ROOT/'outputs/lumine-rebuild-20261016/canonical-v4'

def main():
    base=json.loads((OUT/'fit/master.json').read_text(encoding='utf-8'))
    original=Image.open(OUT/base['file']).convert('RGBA')
    # Explicit candidate palette: separate warm hair/gold, peach skin and cool cloth.
    # Index ownership is retained; this is color grading, not semantic re-segmentation.
    palette=[[255,253,244],[195,151,108],[85,112,153],[166,171,187],
             [248,222,181],[100,76,67],[233,194,144],[69,49,45],
             [184,131,60],[240,235,225],[135,157,188],[145,93,48],
             [151,142,144],[110,93,91],[147,119,104],[205,214,227],
             [247,197,170],[235,241,252],[19,21,30]]
    result=render(base['rects'],palette,original.width,original.height)
    # Exact pixel ownership, transparency and rectangle geometry must stay unchanged.
    a=np.asarray(original);b=np.asarray(result)
    assert np.array_equal(a[:,:,3],b[:,:,3])
    for old,new in zip(base['palette'],palette):
        mask=np.all(a[:,:,:3]==old,axis=2)&(a[:,:,3]>0)
        assert np.all(b[mask,:3]==new)
    result.save(OUT/'fit/master-contrast.png')
    meta={**base,'file':'fit/master-contrast.png','palette':palette,
          'status':'color contrast candidate; user acceptance pending',
          'rectangles':len(base['rects']),'samplingChanged':False,
          'geometryChanged':False,'sourceChanged':False,
          'limitation':'Original palette indices can mix materials; color grading does not restore lost source lines.'}
    (OUT/'fit/master-contrast.json').write_text(json.dumps(meta,ensure_ascii=False),encoding='utf-8')
    board=Image.new('RGB',(640,390),'#263454');d=ImageDraw.Draw(board)
    for i,(im,label) in enumerate([(original,'A Previous palette / 628'),(result,'B Separated tones / 628')]):
        im=im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST)
        board.paste(im,(i*320+(320-im.width)//2,30),im)
        d.text((i*320+12,10),label,fill='white')
    board.save(OUT/'palette-comparison.png')
    print('628 rectangles retained; alpha and pixel ownership verified; no live replacement')

if __name__=='__main__':main()
