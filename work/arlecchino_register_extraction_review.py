from pathlib import Path
import json
p=Path('outputs/arlecchino-actions-20261011/source-calibration.json');d=json.loads(p.read_text(encoding='utf-8'));d['heavy-hook-v2']['excludedSourceRects']=[[656,679,686,706]];d['heavy-hook-v2']['excludedReason']='reviewed isolated dark background remnant below blade, outside character/weapon';p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
