from pathlib import Path
import json,hashlib,re,os
R=Path(__file__).resolve().parents[1]
A=R/'outputs/archive/20261013_stable_gfv2_p6'
D=R/'docs/current/稳定版资料_20261013'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
# Frozen copies use links relative to their own directory.
for p in D.glob('*.md'):
    target=A/'docs'/p.name
    def link(m):
        ref=m[2]
        if '://' in ref or ref.startswith('#'): return m[0]
        original=(p.parent/ref).resolve()
        if original.parent==D.resolve(): original=A/'docs'/original.name
        return '['+m[1]+']('+Path(os.path.relpath(original,target.parent)).as_posix()+')'
    target.write_text(re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,p.read_text(encoding='utf-8')),encoding='utf-8')
errors=[]
for folder in [D,A/'docs']:
    for p in folder.glob('*.md'):
        text=p.read_text(encoding='utf-8')
        assert not re.search(r'[A-Z]:[\\/]Users[\\/]|UID\s*[:：]\s*\d+',text),p
        for label,ref in re.findall(r'\[([^\]]+)\]\(([^)]+)\)',text):
            if '://' not in ref and not ref.startswith('#') and not (p.parent/ref).exists():errors.append((p.name,ref))
assert not errors,errors
m=json.loads((A/'manifest.json').read_text(encoding='utf-8'))
for f in m['files']:
    p=A/f['path']
    if f['path'].startswith('docs/'):
        f.update(bytes=p.stat().st_size,sha256=sha(p))
    else: assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],p
assert sha(A/'release/gia/gpt_20261013_车轮战先匹配_复用GFV2_仅脚本.gia')=='dc778fecee49b58778863359d2e4034c985262e4515928eab4077b926dd04a99'
for p in (R/'runtime/source').rglob('*'):
    if p.is_file(): assert sha(p)==sha(A/'runtime/source'/p.relative_to(R/'runtime/source'))
(A/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'snapshotVerified':len(m['files']),'documentLinks':'passed','privacyScanNewDocs':'passed','releaseHashUnchanged':True,'runtimeSourceUnchanged':True}))
