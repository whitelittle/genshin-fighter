"""Rebuild this self-contained source snapshot without modifying daily sources."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'merge-audit.json').read_text(encoding='utf-8'))
order=json.loads((ROOT/'source/order.json').read_text(encoding='utf-8'))
for name,digest in manifest['sourceFiles'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
code='\n'.join((ROOT/name).read_text(encoding='utf-8') for name in order)
data=code.replace('\n','\r\n').encode() # snapshot/export follows Windows write_text newline behavior
assert hashlib.sha256(data).hexdigest()==manifest['sha256'],'snapshot assembly differs'
(ROOT/'genshin_fighter.lua').write_bytes(data)
print(manifest['sha256'])
