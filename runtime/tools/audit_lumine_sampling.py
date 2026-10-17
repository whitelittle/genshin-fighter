"""Controlled offline sampling comparison; never changes the live art bank."""
from pathlib import Path
import sys, json, base64
import numpy as np
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'game/tools'))
sys.path.insert(0, str(ROOT/'runtime/tools'))
sys.path.insert(0, str(ROOT/'work/optimization-test-deps'))
import artlib as A
from compact_assets import LuaRuntime, python_table

def main():
    art = ROOT/'outputs/lumine-rebuild-20261016'
    out = art/'sampling-audit'; out.mkdir(exist_ok=True)
    meta = json.loads((art/'import.json').read_text(encoding='utf-8'))
    raw = {k: Image.open(art/'source'/v['source']).convert('RGBA').crop(v['bbox']) for k,v in meta['frames'].items()}
    variants = {}
    for name, height, area in [('nearest84',84,False), ('area84',84,True), ('area64',64,True)]:
        scale = height/meta['masterHeightSourcePixels']
        small = {k: A.downscale(im,scale) if area else im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST) for k,im in raw.items()}
        pal = A.build_palette(list(small.values()),16,seed=21)
        variants[name] = {}
        for key, im in small.items():
            idx = A.apply_palette(im,pal)
            before = idx.copy()
            if area: idx = A.despeckle(idx)
            rects = A.painter(idx)
            result = A.render(rects,pal,im.width,im.height)
            result.save(out/f'{name}-{key}.png')
            variants[name][key] = {'size':im.size,'rectangles':len(rects),'cleanupChangedPixels':int(np.count_nonzero(before!=idx))}
            if name=='nearest84':
                assert np.array_equal(np.asarray(result),np.asarray(Image.open(art/'fit'/f'{key}.png').convert('RGBA'))),key
    rt=LuaRuntime(); rt.execute('__loaders={};'+(ROOT/'runtime/source/assets/gf_art_nahida.lua').read_text(encoding='utf-8'))
    nahida=python_table(rt.globals().__loaders['gf_art_nahida']())
    tier=nahida['lo']; pose=tier['idle']; pal=np.frombuffer(base64.b64decode(tier['pal']),dtype=np.uint8).reshape(-1,3).tolist()
    rects=np.frombuffer(base64.b64decode(pose['d']),dtype=np.uint8)[:pose['n']*5].reshape(-1,5).tolist()
    A.render(rects,pal,pose['w'],pose['h']).save(out/'nahida-runtime-lo-idle.png')
    board=Image.new('RGB',(1000,750),'#263454'); draw=ImageDraw.Draw(board)
    for col,(name,label) in enumerate([('nearest84','A Current / 84px'),('area84','B Area / 84px'),('area64','C Area / 64px')]):
        draw.text((col*250+12,12),label,fill='white')
        for row,key in enumerate(['idle_0','walk_1','walk_3']):
            im=Image.open(out/f'{name}-{key}.png'); factor=185/(84 if name!='area64' else 64)
            im=im.resize((round(im.width*factor),round(im.height*factor)),Image.Resampling.NEAREST)
            board.paste(im,(col*250+(250-im.width)//2,42+row*230+185-im.height),im)
            draw.text((col*250+12,232+row*230),f'{key}: {variants[name][key]["rectangles"]} rects',fill='white')
    im=Image.open(out/'nahida-runtime-lo-idle.png'); im=im.resize((round(im.width*185/im.height),185),Image.Resampling.NEAREST)
    board.paste(im,(765,42),im); draw.text((762,12),'D Nahida lo / 55px',fill='white')
    draw.text((762,242),'Equal height for comparison',fill='white')
    board.save(out/'comparison.png')
    (out/'metrics.json').write_text(json.dumps({'variants':variants,'nahidaLoIdle':{k:pose[k] for k in ['w','h','n','u']},'scope':'offline comparison only; no anatomy correction or live replacement'},indent=2),encoding='utf-8')
    print(json.dumps({k:{'idle':v['idle_0'],'peak':max(f['rectangles'] for f in v.values())} for k,v in variants.items()}))

if __name__=='__main__': main()
