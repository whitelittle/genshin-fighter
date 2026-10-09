"""Restore the isolated V4 handoff; never overwrites an existing folder."""
from pathlib import Path
import hashlib,json,zipfile
r=Path(__file__).resolve().parent
m=json.loads((r/'V4_HANDOFF_MANIFEST.json').read_text())
target=r/'v4-handoff-20261009'
if target.exists(): raise SystemExit('Target already exists; choose a fresh directory.')
archive=r/'V4_HANDOFF_RESTORED.zip'
with archive.open('wb') as f:
    for x in m['parts']:
        b=(r/x['name']).read_bytes()
        assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'],x['name']
        f.write(b)
assert hashlib.sha256(archive.read_bytes()).hexdigest()==m['archive_sha256']
with zipfile.ZipFile(archive) as z:
    for n in z.namelist():
        assert not Path(n).is_absolute() and '..' not in Path(n).parts,n
    z.extractall(target)
print('Restored:',target)
print('Next: python3',target/'tools/verify_handoff.py')
