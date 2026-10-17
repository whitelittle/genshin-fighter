from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'MANIFEST.json').read_text())
for file in manifest['files']:
 p=root/file['path']
 assert p.stat().st_size==file['bytes'],str(p)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==file['sha256'],str(p)
print('Verified',len(manifest['files']),'indexed files')
