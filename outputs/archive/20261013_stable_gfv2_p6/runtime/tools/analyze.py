"""Readable module map and conservative asset storage estimates (no compression)."""
from pathlib import Path
import json,re,base64
ROOT=Path(__file__).resolve().parents[1]
def analyze():
    manifest=json.loads((ROOT/'dist/build.json').read_text(encoding='utf-8'))
    modules={};domains={}
    for name,path in manifest['modules'].items():
        code=(ROOT/path).read_text(encoding='utf-8')
        deps=sorted(set(re.findall(r"require\(['\"]([^'\"]+)['\"]\)",code)))
        domain=Path(path).parts[1]
        modules[name]={'path':path,'lines':len(code.splitlines()),'bytes':len(code.encode('utf-8')),
                       'requires':deps,'dynamicRequire':bool(re.search(r"require\([^'\"]",code))}
        d=domains.setdefault(domain,{'files':0,'bytes':0});d['files']+=1;d['bytes']+=modules[name]['bytes']
    furina=(ROOT/'source/assets/gf_furina_data.lua').read_text(encoding='utf-8')
    # Generated data is JSON-like Lua; this estimate inspects encoded payloads only.
    payloads=re.findall(r'\["d"\]="([A-Za-z0-9+/]+)"',furina)
    raw=[base64.b64decode(p) for p in payloads]
    receipt=json.loads((ROOT/'furina-import.json').read_text(encoding='utf-8'))
    palettes=set();all8=0;rects=0
    for row in receipt['sources']:
        meta=json.loads((ROOT.parent/row['rectsFile']).read_text(encoding='utf-8'))
        palettes.add(json.dumps(meta['palette'],sort_keys=True))
    # Unique data blocks, not repeated display references, determine storage.
    for block in raw:
        import struct
        n=len(block)//10;vals=struct.unpack('<'+'H'*(n*5),block[:n*10])
        rects+=n
        if all(v<=255 for v in vals):all8+=1
    result={'moduleCount':len(modules),'domains':domains,'modules':modules,
        'furinaStorage':{'uniqueBodyFrames':receipt['uniqueBodyFrames'],'encodedFramesIncludingAuxiliary':len(raw),'displayStates':receipt['displayStates'],
        'rectangles':rects,'rawUint16BytesWithPadding':sum(map(len,raw)),
        'base64Characters':sum(map(len,payloads)),'uniquePalettesInSource':len(palettes),
        'framesEligibleForUint8':all8,'luaDataFileBytes':len(furina.encode('utf-8'))},
        'scope':'static estimates; no load-time, memory or device-frame-rate claim'}
    ayaka= (ROOT/'source/assets/gf_ayaka_data.lua').read_text(encoding='utf-8')
    payloads=re.findall(r'\["d"\]="([A-Za-z0-9+/]+)"',ayaka)
    raw=[base64.b64decode(p) for p in payloads]
    receipt=json.loads((ROOT/'ayaka-import.json').read_text(encoding='utf-8'))
    palettes={json.dumps(json.loads((ROOT.parent/row['rectsFile']).read_text(encoding='utf-8'))['palette'],sort_keys=True) for row in receipt['sources']}
    count8=0;rects=0
    for block in raw:
        n=len(block)//10;vals=struct.unpack('<'+'H'*(n*5),block[:n*10]);rects+=n
        count8+=all(v<=255 for v in vals)
    result['ayakaStorage']={'uniqueBodyFrames':receipt['uniqueBodyFrames'],'encodedFramesIncludingAuxiliary':len(raw),'displayStates':receipt['displayStates'],
        'rectangles':rects,'rawUint16BytesWithPadding':sum(map(len,raw)),'base64Characters':sum(map(len,payloads)),
        'uniquePalettesInSource':len(palettes),'framesEligibleForUint8':count8,'luaDataFileBytes':len(ayaka.encode('utf-8'))}
    path=ROOT/'verification/module-map.json';path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'domains':domains,'furinaStorage':result['furinaStorage'],'ayakaStorage':result['ayakaStorage']},ensure_ascii=False,indent=2))
if __name__=='__main__':analyze()
