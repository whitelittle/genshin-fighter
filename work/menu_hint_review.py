from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'runtime/tests'))
from mock_flow import RuntimeClient,wait
O=R/'outputs/menu-hint-20261014';RuntimeClient.source=O/'stable/genshin_fighter.lua';rows=[]
for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(1600,900)),('Mobile',(900,1600)),('Controller',(1600,900))]:
 c=RuntimeClient(device=device,canvas=canvas);c.env.GF_FIRST_SCENE='menu'
 wait(c,"GF_APP() and GF_APP().sceneName=='menu' and not GF_APP().poolNext and not GF_APP().trans");c.run(.8);c.render(O/f'menu-{device}-{canvas[0]}.png')
 c.lua("(function()GF_APP():go('fight',{chars={'clorinde','arlecchino'},mode='training',cpu={false,false},infinite=true,time=99});return true end)()")
 wait(c,"GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().poolNext");c.run(1)
 c.render(O/f'fight-{device}-{canvas[0]}.png')
 if device=='Mobile':x,y=canvas[0]/2,canvas[1]-264*c.lua('GF_APP().s')
 else:x,y=canvas[0]/2-5*c.lua('GF_APP().s'),28*c.lua('GF_APP().s')
 c.touch('down',x,y);c.step();c.touch('up',x,y);c.run(.2);assert c.lua('GF_APP().scene.paused'),(device,canvas,x,y)
 assert not list(c.H.err.values());rows.append({'device':device,'canvas':canvas,'menuHintClickOpensBattleMenu':True})
 print(device,canvas,'hint and clickable entry passed',flush=True)
(O/'menu-hint-verification.json').write_text(json.dumps({'scope':'mock UI, not native device','rows':rows},indent=2),encoding='utf8')
