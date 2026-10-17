from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'runtime/tests'))
from mock_flow import RuntimeClient,wait
O=R/'outputs/arlecchino-scale-layer-20261014';RuntimeClient.source=O/'release/genshin_fighter.lua';checks=[]
for device in ['KeyboardAndMouse','Mobile']:
 c=RuntimeClient(device=device,canvas=(1600,900));c.env.GF_FIRST_SCENE='menu'
 wait(c,"GF_APP() and GF_APP().sceneName=='menu' and not GF_APP().poolNext");c.run(.5)
 c.lua("(function()GF_APP().scene:tutorialMenu();assert(#GF_APP().scene.items==2 and GF_APP().scene.items[1].id=='howto');return true end)()")
 checks.append({'device':device,'tutorialDuplicateTrainingRemoved':True})
 c.lua("(function()GF_APP():go('select',{mode='training',cpu=false,previewRoster=false});return true end)()")
 wait(c,"GF_APP().sceneName=='select' and GF_APP().scene.built==6 and not GF_APP().poolNext")
 c.lua("(function()local s=GF_APP().scene;s.cur[1]=6;s:confirm(1);assert(s:activePlayer()==2 and not s.done[2] and s.phase=='chars');return true end)()")
 c.run(.3);c.render(O/f'training-select-2p-{device}.png')
 c.lua("(function()local s=GF_APP().scene;s.cur[2]=6;s:confirm(2);return true end)()")
 wait(c,"GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
 assert c.lua("GF_APP().scene.sim.f[1].key=='arlecchino' and GF_APP().scene.sim.f[2].key=='arlecchino'")
 checks.append({'device':device,'trainingSameCharacter2PSelectionPassed':True})
 # Diagnostic pose freeze uses real renderer/provider, without claiming battle damage.
 c.lua("(function()local s=GF_APP().scene;s.sim.phase='fight';s.sim.freeze=100000;local p=s.sim.f[1];p.state='burst';p.t=80;p.cinematicConfirmed=true;p.move=p.kit.burst;p.x=-15000;p.y=0;p.face=1;local d=s.sim.f[2];d.x=15000;d.y=0;d.state='idle';return true end)()")
 c.run(1)
 assert c.lua("GF_APP().scene.views[1].characterChannels[1].front.node.parent==GF_APP().scene.lay.ghost")
 c.render(O/f'burst-wings-behind-{device}.png');checks.append({'device':device,'burstWingsParentBehindBody':True})
 c.lua("(function()local s=GF_APP().scene;local p=s.sim.f[1];p.state='attack';p.moveId='heavy';p.move=p.kit.weapon.heavy;p.t=20;p.cinematicConfirmed=false;return true end)()")
 c.run(.5)
 assert c.lua("GF_APP().scene.views[1].characterChannels[1].slots[1].node.parent==GF_APP().scene.lay.fx")
 checks.append({'device':device,'attackChannelReturnsForeground':True})
 receipt=json.loads((R/'runtime/arlecchino-import.json').read_text(encoding='utf8'));art=c.lua("GF_REQUIRE('gf_art')")
 for row in receipt['sources']:
  if not row['pose'].startswith('walk_'):continue
  original=np.array(Image.open(R/row['file']).convert('RGBA'));rebuilt=np.zeros_like(original);img=art.pose('arlecchino','lo',row['pose']);u=row['scale']
  for n in range(img.n):
   off=n*5;x,y,w,h=[round(img.bytes[off+j]/u) for j in range(1,5)];color=img.pal[int(img.bytes[off+5])+1];rebuilt[y:y+h,x:x+w]=[color[j] for j in range(1,5)]
  assert np.array_equal(original,rebuilt),row['pose']
 checks.append({'device':device,'sixNewWalkPixelsExact':True})
 c.lua("(function()GF_APP():go('howto');return true end)()")
 wait(c,"GF_APP().sceneName=='howto' and not GF_APP().poolNext");c.run(.6)
 for page in range(1,5):
  c.lua(f"(function()GF_APP().input.menuQ={{'howto:{page}'}};return true end)()");c.run(.5);assert c.lua('GF_APP().scene.page')==page;c.render(O/f'howto-{device}-{page}.png')
  checks.append({'device':device,'howtoPage':page,'directTabPassed':True})
 assert not list(c.H.err.values())
(O/'revision-checks.json').write_text(json.dumps({'scope':'PC and mobile landscape mock; visual candidate, not native acceptance','checks':checks},indent=2),encoding='utf8');print('revision checks',len(checks))
