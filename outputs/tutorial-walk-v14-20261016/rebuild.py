"""Reassemble this isolated source snapshot and verify its recorded digest."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'build-manifest.json').read_text(encoding='utf-8'))
order=json.loads((ROOT/'source/order.json').read_text(encoding='utf-8'))
for path,digest in manifest['sourceFiles'].items():
 assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
code='\n'.join((ROOT/path).read_text(encoding='utf-8') for path in order)
data=code.replace('\n','\r\n').encode('utf-8')
assert hashlib.sha256(data).hexdigest()==manifest['clientSha256']
(ROOT/'genshin_fighter.lua').write_bytes(data)
print(manifest['clientSha256'])
