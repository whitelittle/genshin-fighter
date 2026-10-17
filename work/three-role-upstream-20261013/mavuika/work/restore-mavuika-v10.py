"""Verify and restore complete Mavuika source; run from this upload directory."""
from pathlib import Path
import hashlib,json,zipfile
root=Path(__file__).resolve().parent
m=json.loads((root/'MAVUIKA_V10_MANIFEST.json').read_text())
for a in m['archives']:
 p=root/a['file'];assert p.stat().st_size==a['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256'],f"Archive mismatch: {p.name}"
for f in m['files']:
 with zipfile.ZipFile(root/f['archive']) as z:
  b=z.read(f['path']);assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],f"File mismatch: {f['path']}"
 p=root/f['path'];assert p.resolve().is_relative_to((root/'mavuika-v10').resolve())
 if p.exists():assert p.read_bytes()==b,f"Refusing to overwrite different file: {p}"
 else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
print(f"Verified and restored {len(m['files'])} files from source {m['sourceCommit']} into mavuika-v10/")
