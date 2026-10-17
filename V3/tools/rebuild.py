from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1]
paths=json.loads((root/'source/order.json').read_text())
assembled=b''.join((root/p).read_bytes() for p in paths)
expected=(root/'client/genshin_fighter.lua').read_bytes()
assert assembled==expected,'source chunks differ from accepted client'
print('Verified byte-identical V3 baseline:',hashlib.sha256(assembled).hexdigest())
