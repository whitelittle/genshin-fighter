"""Local delivery archive with verified Lua/GIA hashes; no external app writes."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[2]
out=ROOT/'outputs/team-battle-20261013'
d=json.loads((out/'delivery.json').read_text(encoding='utf-8'))
for row in d['files']:
    raw=(out/row['filename']).read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
n=json.loads((out/'native-node-verification.json').read_text(encoding='utf-8'))
node=out/'gpt_20261013_三人车轮战_GF3独立节点.gia'
assert hashlib.sha256(node.read_bytes()).hexdigest()==n['sha256']
for name in ['logic.json','compact-assets.json','mock-flow.json']:
    report=json.loads((out/name).read_text(encoding='utf-8'))
    assert report.get('clientSha256',report.get('sourceSha256'))==d['sourceSha256'],name
files=[out/r['filename'] for r in d['files']]+[node,out/'安装与验证说明.md',out/'delivery.json',out/'native-node-verification.json']
for name in ['logic.json','compact-assets.json','mock-flow.json','team-flow.json','new-role-pool.json','performance.json']:
    files.append(out/name)
for name in ['team-battle.json','team-net.json']:
    files.append(ROOT/'runtime/verification'/name)
files.append(ROOT/'outputs/six-character-size-20261013/size-audit.json')
archive=out/'六角色统一尺度_三人车轮战_GIA交付.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in files:
        z.write(p,('验证/'+p.name) if p.suffix=='.json' and p.name!='delivery.json' else p.name)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for row in d['files']:
        assert hashlib.sha256(z.read(row['filename'])).hexdigest()==row['sha256']
print(json.dumps({'archive':archive.name,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':len(files),'giaAndLuaHashesVerified':True},ensure_ascii=False))
