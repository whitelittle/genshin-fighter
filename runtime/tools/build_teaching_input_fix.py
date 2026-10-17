"""Isolated keyboard-release fix, preserving the entire teaching v14 art and rules."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/tutorial-walk-v14-20261016'
OUT=ROOT/'outputs/tutorial-input-v15-20261016'

def build():
 shutil.copytree(BASE/'source',OUT/'source',dirs_exist_ok=True)
 p=OUT/'source/input/gf_input.lua'
 code=p.read_text(encoding='utf-8')
 old="""function I:key(b, down)
    local p, bit, menu = b[2], b[3], b[4]"""
 new="""function I:key(b, down)
    -- Key events describe a physical state, not an additional held key.
    -- Deduplicate each binding while retaining counts for aliases (E/I, W/Space).
    self.keyDown = self.keyDown or {}
    local was = self.keyDown[b[1]] == true
    if down == was then return end
    self.keyDown[b[1]] = down or nil
    local p, bit, menu = b[2], b[3], b[4]"""
 assert code.count(old)==1
 p.write_text(code.replace(old,new),encoding='utf-8')
 order=json.loads((BASE/'source/order.json').read_text(encoding='utf-8'))
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 changed=[p for p in order if sha(BASE/p)!=sha(OUT/p)]
 assert changed==['source/input/gf_input.lua'],changed
 (OUT/'genshin_fighter.lua').write_text('\n'.join((OUT/p).read_text(encoding='utf-8') for p in order),encoding='utf-8')
 (OUT/'verification').mkdir(exist_ok=True)
 manifest={'clientSha256':sha(OUT/'genshin_fighter.lua'),'baselineSha256':sha(BASE/'genshin_fighter.lua'),'onlyChangedSourceFiles':changed,'sourceFiles':{p:sha(OUT/p) for p in order}}
 (OUT/'build-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in manifest.items() if k!='sourceFiles'}))
 return OUT

if __name__=='__main__':build()
