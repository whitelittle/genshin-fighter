from pathlib import Path
import json
p=Path('outputs/arlecchino-actions-20261011/source-calibration.json');d=json.loads(p.read_text(encoding='utf-8'));d['throw-low-push-v2']={'supportY':[708,716,1446,1443]};p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
p=Path('work/arlecchino_fit_initial.py');s=p.read_text(encoding='utf-8').replace("isolate('source/throw-low-v1.png',4,'throw-low-v1'", "isolate('source/throw-low-push-v2.png',4,'throw-low-push-v2'");p.write_text(s,encoding='utf-8')
p=Path('work/arlecchino_pairing_profiles.py');s=p.read_text(encoding='utf-8').replace('(619, 1050)','(566, 1090)').replace('(619,1050)','(566,1090)');s=s.replace(" for ny in range(max(0,base[1]-10),min(ni.shape[0],base[1]+11)):", " nyRange=range(max(0,base[1]-10),min(ni.shape[0],base[1]+11))\n if '/nahida/victim_0' in native['file']:nyRange=range(23,28)\n if '/raiden/victim_0' in native['file']:nyRange=range(20,27)\n for ny in nyRange:")
p.write_text(s,encoding='utf-8')
