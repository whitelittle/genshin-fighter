"""New movement banks must actually be presented at both host rates."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-polish-v13-20261016';E=OUT/'verification';E.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'runtime/tests'))
from mock_flow import RuntimeClient,wait
RuntimeClient.source=OUT/'genshin_fighter.lua';rows=[]
for device,hz in [('KeyboardAndMouse',60),('Mobile',60),('KeyboardAndMouse',30),('Mobile',30)]:
 c=RuntimeClient(device=device,canvas=(1600,900));c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 def reset():
  c.lua("(function()local s=GF_APP().scene;local a,b=s.sim.f[1],s.sim.f[2];s.sim:setState(a,'idle');s.sim:setState(b,'idle');a.x=-45000;b.x=65000;a.vx=0;a.face=1;a.inPrev=0;a.releaseMask=0;a.lastFwd=-100;a.lastBack=-100;return true end)()")
  c.run(.2)
 def pose():return c.lua('GF_APP().scene.views[1].front and GF_APP().scene.views[1].front.key')
 for group,key in [('walk','D'),('back','A'),('dash','U')]:
  reset();c.key(key,True);c.step(1/hz)
  if group=='dash':c.key(key,False)
  seen=[];log=[]
  for tick in range(90 if group!='dash' else 30):
   c.step(1/hz);name=pose();log.append(name)
   if name and name.startswith('dash_' if group=='dash' else 'walk_') and name not in seen:
    seen.append(name)
    if hz==60:c.render(E/f'new-{group}-{name}-{device}.png')
  c.key(key,False);c.run(.3)
  assert set(seen)=={f'{"dash" if group=="dash" else "walk"}_{i}'for i in range(4)},(device,hz,group,seen,log)
  assert pose()=='idle_0',(group,pose())
  rows.append({'device':device,'hostHz':hz,'motion':group,'actuallyPresented':seen,'idleReturned':True,'maxInstructions':c.max_instr});print(json.dumps(rows[-1]),flush=True)
meta=json.loads((ROOT/'outputs/lumine-rebuild-20261016/import.json').read_text(encoding='utf-8'));assert meta['bodyUniqueMean']<1000
(E/'rebuild-checks.json').write_text(json.dumps({'clientSha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'mockOnly':True,'rows':rows,'art':meta,'scope':'presentation/input probe; not human aesthetic or native acceptance'},ensure_ascii=False,indent=2),encoding='utf-8')
