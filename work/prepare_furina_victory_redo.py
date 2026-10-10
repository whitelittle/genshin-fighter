from pathlib import Path
import json, hashlib
from build_ayaka_attacks import extract
R=Path(__file__).resolve().parents[1];O=R/'outputs/furina-design-20261010'
rows=extract(O/'victory-curtaincall-source-v2.png',4)
for i,(box,im,xs,ys) in enumerate(rows):im.save(O/f'victory-v2-source-{i}.png')
meta={'source':'victory-curtaincall-source-v2.png','sourceSha256':hashlib.sha256((O/'victory-curtaincall-source-v2.png').read_bytes()).hexdigest(),
      'rois':[list(r[0]) for r in rows],'calibrationUprightSourceHeight':rows[0][1].height,
      'newDisplaySourceIndices':[1,2],'firstLast':'exact idle reuse','anatomicalAcceptance':False}
(O/'victory-v2-extraction.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(meta,ensure_ascii=False))
