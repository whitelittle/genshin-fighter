from pathlib import Path
import json
p=Path('outputs/arlecchino-actions-20261011/additional-body-plans.json');d=json.loads(p.read_text(encoding='utf-8'))
for a in d:
 if a['key'] in {'light3','heavy','crouchheavy'}:a['unit']={'light3':.78,'heavy':.70,'crouchheavy':.63}[a['key']]
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
