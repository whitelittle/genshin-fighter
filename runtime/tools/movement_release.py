"""Apply only five rendering chunks to the frozen four-character native release."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent/'outputs/all-codec-comparison-20261012_053101'
OUT=ROOT.parent/'outputs/movement-fix-20261013'
OUT.mkdir(exist_ok=True)
manifest=json.loads((BASE/'comparison.json').read_text(encoding='utf-8'))['ordinary']
data=(BASE/'保留的普通可读版.lua').read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(data)==manifest['sha256']
paths={'source/render/gf_gfx.lua','source/render/gf_fview.lua','source/characters/gf_character_furina.lua',
       'source/characters/gf_character_ayaka.lua','source/battle/gf_battle_loading.lua'}
working=(ROOT.parent/'outputs/smooth-comparison-20261013/working-source.lua').read_bytes()
parts=[];originals=[];chunks=[];changes=[];offset=0
for row in manifest['chunks']:
 old=data[offset:offset+row['bytes']];offset+=row['bytes'];assert sha(old)==row['sha256']
 new=(ROOT/row['path']).read_bytes() if row['path'] in paths else old
 if row['path'] in paths:
  # These exact pre-edit chunks are also in the captured editable-source baseline.
  assert old in working,('pre-edit source differs from native release',row['path'])
  changes.append({'path':row['path'],'oldSha256':sha(old),'newSha256':sha(new)})
 parts.append(new);originals.append(old);chunks.append({'path':row['path'],'bytes':len(new),'sha256':sha(new)})
assert offset==len(data) and len(changes)==5 and b''.join(originals)==data
patched=b''.join(parts);script=OUT/'genshin_fighter.lua';script.write_bytes(patched)
receipt=dict(manifest,release='movement-render-fix-20261013',bytes=len(patched),sha256=sha(patched),chunks=chunks,
             frozenBaseSha256=sha(data),changedChunks=changes,onlyRenderingChanged=True,nativeTested=False)
(OUT/'build.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'bytes':len(patched),'sha256':sha(patched),'changedChunks':len(changes),'onlyRenderingChanged':True}))
