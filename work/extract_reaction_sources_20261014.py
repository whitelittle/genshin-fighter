from pathlib import Path
import json,os,shutil
import clorinde_assets as ca
R=Path(__file__).resolve().parents[1];O=R/'outputs/three-role-redesign-20261014';plans=json.loads((R/'work/reaction_chain_20261014_selected.json').read_text(encoding='utf8'))
for p in plans:
 D=O/p['role'];src=D/'sources/hit-knockdown-20261014.png';shutil.copy2(os.path.expandvars(p['generatedPath']),src)
 (D/'prompts/hit-knockdown-20261014.txt').write_text(p['prompt'],encoding='utf8')
 if p.get('firstPath'):
  (D/'history').mkdir(exist_ok=True);shutil.copy2(os.path.expandvars(p['firstPath']),D/'history/hit-knockdown-spacing-rejected.png');(D/'prompts/hit-knockdown-spacing-20261014.txt').write_text(p['spacingPrompt'],encoding='utf8')
 items,fragments=ca.extract(src,6)
 for i,(im,info) in enumerate(items):
  assert not info['fullCanvasContact'],(p['role'],i)
  im.save(D/f'frames/hit-knockdown-raw-20261014-{i}.png')
 (D/'reaction-source-regions-20261014.json').write_text(json.dumps([info for im,info in items],ensure_ascii=False,indent=2),encoding='utf8')
 print(p['role'],'6 bodies, shared down = pose5')
