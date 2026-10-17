"""Independent Clorinde action inventory. Never modifies restored V4 or other fighters."""
from pathlib import Path
import json, hashlib
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'work/v4-handoff-20261009-partial'
OUT=ROOT/'outputs/arlecchino-actions-20261011'

def main():
    overlay=json.loads((OLD/'V4/design/CODEX_CURRENT_OVERLAY_20261009.json').read_text(encoding='utf-8'))
    rows=[]
    for entry in overlay['entries']:
        if entry['character']!='arlecchino':continue
        paths=([entry['codex_preferred_candidate']] if entry.get('codex_preferred_candidate') else
               [entry['new_source']] if entry.get('new_source') else entry.get('existing_sources',[]))
        sources=[]
        for rel in paths:
            p=OLD/rel
            if not p.exists():raise FileNotFoundError(rel)
            with Image.open(p) as im:
                im.load()
                sources.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                    'size':list(im.size),'alphaExtrema':list(im.convert('RGBA').getchannel('A').getextrema())})
        rows.append({'actionId':entry['actionId'],'group':entry['group'],'legacySources':sources,
            'status':'历史候选待复核' if sources else '缺源图，待制作',
            'legacyStatus':entry['source_status'],'visualAccepted':False,'runtimeIntegrated':False})
    report={'character':'arlecchino','date':'2026-10-11','actions':rows,
        'sourceCoveredGroups':sum(bool(r['legacySources']) for r in rows),
        'missingGroups':[r['group'] for r in rows if not r['legacySources']],
        'verification':'source file and PNG only','simulation':'not run','device':'not observed'}
    (OUT/'legacy-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='actions'},ensure_ascii=False))

if __name__=='__main__':main()
