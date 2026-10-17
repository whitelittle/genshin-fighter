from pathlib import Path
import json
p=Path('outputs/arlecchino-actions-20261011');d=json.loads((p/'actions.json').read_text(encoding='utf-8'));count=f"{len(d)}组/{sum(len(v['frames']) for v in d.values())}姿"
for f in [p/'player.html',p/'index.html']:
 s=f.read_text(encoding='utf-8').replace('9组/42姿',count);f.write_text(s,encoding='utf-8')
print(count)
