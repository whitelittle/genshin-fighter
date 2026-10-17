"""Assemble editable Lua modules into one importable script. No minification."""
from pathlib import Path
import hashlib,json,re

ROOT=Path(__file__).resolve().parents[1]
def build():
    order=json.loads((ROOT/'source/order.json').read_text(encoding='utf-8'))
    chunks=[];modules={};entries=[]
    for rel in order:
        path=(ROOT/rel).resolve()
        assert path.is_relative_to(ROOT/'source'),rel
        raw=path.read_bytes();code=raw.decode('utf-8')
        for key in re.findall(r"__loaders\[['\"]([^'\"]+)['\"]\]\s*=",code):
            assert key not in modules,'duplicate loader '+key
            modules[key]=rel
        chunks.append(raw)
        entries.append({'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    assert order[0]=='source/prefix.lua' and order[-1]=='source/bootstrap.lua'
    client=b''.join(chunks)
    out=ROOT/'dist';out.mkdir(exist_ok=True)
    (out/'genshin_fighter.lua').write_bytes(client)
    manifest={'release':'structure-20261011-four-character-candidate','minified':False,'bytes':len(client),
              'sha256':hashlib.sha256(client).hexdigest(),'modules':modules,'chunks':entries}
    (out/'build.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'modules':len(modules),'bytes':len(client),'sha256':manifest['sha256']}))
    return manifest
if __name__=='__main__':build()
