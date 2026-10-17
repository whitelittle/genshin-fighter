from pathlib import Path
import json
p=Path('outputs/arlecchino-actions-20261011');f=p/'source-calibration.json';c=json.loads(f.read_text(encoding='utf-8'));c['heavy-effective-single-v4']={'supportY':[905]};f.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8');f=p/'additional-body-plans.json';plans=json.loads(f.read_text(encoding='utf-8'));next(x for x in plans if x['key']=='heavy')['unit']=.80;f.write_text(json.dumps(plans,ensure_ascii=False,indent=2),encoding='utf-8')
