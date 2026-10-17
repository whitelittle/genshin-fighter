from pathlib import Path
import json, shutil, hashlib
root = Path(__file__).resolve().parent
manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
generated = Path.home()/'.codex'/'generated_images'/'01a13b51-6873-7302-b0af-bbcbe55958f7'
for item in manifest['items']:
    dest = root/item['source']
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(generated/item['generatedFile'], dest)
    item['sha256'] = hashlib.sha256(dest.read_bytes()).hexdigest()
(root/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print('Saved',len(manifest['items']),'source boards with SHA256')
