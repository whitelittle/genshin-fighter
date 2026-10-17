from pathlib import Path
import json,shutil
r=Path.cwd();p=r/'outputs/arlecchino-actions-20261011';base=r/'outputs/v4-one-character-20261010/baseline-actions';d=json.loads((base/'parameters.json').read_text(encoding='utf-8'));m=json.loads((p/'opponent-models.json').read_text(encoding='utf-8'))
for model,char in [('raiden','raidenshogun'),('nahida','nahida')]:
 for f in d['characters'][char]['poses']:
  if f['origin']!='keyframes' or f['pose'] not in ['guard_1','guard_2']:continue
  name=f['pose'];dest=p/'opponent'/model/(name+'.png');shutil.copy2(base/f['file'],dest);m[model][name]={'file':dest.relative_to(p).as_posix(),'ax':f['ax'],'ay':f['ay'],'scale':f['u'],'nativeUnitRetained':True,'width':f['w'],'height':f['h'],'sourceHash':f['png_sha256']}
(p/'opponent-models.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8');(p/'opponent-data.js').write_text('window.ARLECCHINO_OPPONENT_MODELS='+json.dumps(m)+';',encoding='utf-8')
p=p/'player-v2.js';s=p.read_text(encoding='utf-8').replace("if(selected==='Q'&&active.branch==='block')key='basic_0'", "if(active.branch==='block'&&(active.events||[]).length&&!['throw','victim'].includes(selected))key='guard_2'");s=s.replace("if(active.branch==='hit'&&dt>=3&&e.kind!=='confirm')effect('impact',foe.x,foe.y-190,(8-dt)/5)", "if(active.branch==='hit'&&dt>=3&&e.kind!=='confirm')effect('impact',foe.x,foe.y-190,(8-dt)/5);if(active.branch==='block'&&dt>=3)effect('guide',foe.x-60,foe.y-210,(8-dt)/5)");p.write_text(s,encoding='utf-8')
