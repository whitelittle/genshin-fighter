from pathlib import Path
import hashlib, json, zipfile
from PIL import Image
root = Path(__file__).resolve().parent
manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
rows = json.loads((root/'finalize.json').read_text(encoding='utf-8'))
for item in rows:
    p = root/item['source']
    item['sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
    with Image.open(p) as im:
        im.verify()
    with Image.open(p) as im:
        item['size'] = list(im.size)
        item['mode'] = im.mode
        item['alphaRange'] = list(im.getchannel('A').getextrema()) if 'A' in im.getbands() else None
manifest['items'] = rows
(root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
archive = root.parent/'tutorial-regular-assets-20261015-v1.zip'
folders = [root,root.parent/'tutorial-paimon-20261015']
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for folder in folders:
        for p in sorted(folder.rglob('*')):
            if p.is_file() and p.suffix not in {'.py','.pyc'} and p.name != 'finalize.json':
                z.write(p,p.relative_to(root.parent))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    count = len(z.namelist())
print(json.dumps({'sourceBoards':len(rows),'archiveFiles':count,'zipBytes':archive.stat().st_size,'zipSha256':hashlib.sha256(archive.read_bytes()).hexdigest()}))
