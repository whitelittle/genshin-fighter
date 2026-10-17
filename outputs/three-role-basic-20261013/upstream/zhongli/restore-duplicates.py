from pathlib import Path
import json,shutil,hashlib
root=Path(__file__).resolve().parent
for item in json.loads((root/'download-materials/duplicate-paths.json').read_text(encoding='utf-8')):
    src=root/item['source'];dst=root/item['path']
    assert hashlib.sha256(src.read_bytes()).hexdigest()==item['sha256'],str(src)
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
print('All duplicate paths restored.')
