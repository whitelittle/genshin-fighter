from pathlib import Path
import json,hashlib
p=Path('outputs/arlecchino-actions-20261011');m=json.loads((p/'manifest.json').read_text(encoding='utf-8'));m['files']={f.relative_to(p).as_posix():{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in p.rglob('*') if f.is_file() and f.name!='manifest.json'};(p/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8');assert len(json.loads((p/'actions.json').read_text(encoding='utf-8')))==25;assert (p/'完整动作候选交付.md').exists();print('Final manifest refreshed after documented rebuild')
