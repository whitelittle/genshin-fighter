from pathlib import Path
import json
p=Path('outputs/arlecchino-actions-20261011/source-calibration.json');d=json.loads(p.read_text(encoding='utf-8'));d['light1-pole-v2']={'bladeCenters':[[186,166],[915,197],[174,704],[940,664]],'bodySeeds':[[478,255],[1240,258],[463,788],[1240,790]],'minBladeArea':6000,'shaftHints':[[[215,110],[720,275]],[[1000,165],[1490,275]],[[228,659],[813,663]],[[977,629],[1455,765]]],'supportY':[512,513,992,1008]};p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
