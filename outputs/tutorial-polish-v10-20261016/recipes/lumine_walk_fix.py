"""Compare presented walk poses, not only the requested animation clock."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-polish-v10-20261016';E=OUT/'verification';E.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'runtime/tests'));sys.path.insert(0,str(ROOT/'runtime/tools'))
from mock_flow import RuntimeClient,wait
rows=[]
for label,source in [('before',ROOT/'outputs/tutorial-complete-v9-20261015/genshin_fighter.lua'),('after',OUT/'genshin_fighter.lua')]:
 RuntimeClient.source=source
 for device,hostHz in [('KeyboardAndMouse',60),('Mobile',60),('KeyboardAndMouse',30),('Mobile',30)]:
  c=RuntimeClient(device=device,canvas=(1600,900));c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','seed':21})
  wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
  for group,key in [('walk','D'),('back','A')]:
   c.lua("(function()local s=GF_APP().scene;local a,b=s.sim.f[1],s.sim.f[2];s.sim:setState(a,'idle');s.sim:setState(b,'idle');a.x=-45000;b.x=65000;a.vx=0;a.face=1;return true end)()")
   c.step();c.key(key,True);seen=set();changes=[];last=None
   for tick in range(160):
    c.step(1/hostHz);pose=c.lua('GF_APP().scene.views[1].front and GF_APP().scene.views[1].front.key')
    if pose and pose.startswith(group+'_'):seen.add(pose)
    if pose!=last:changes.append([tick,pose]);last=pose
    if label=='after' and tick==35 and hostHz==30:c.render(E/f'walk-{group}-{device}.png')
   c.key(key,False);c.run(.3)
   assert c.lua("GF_APP().scene.sim.f[1].state=='idle'")
   if label=='after':assert len(seen)==8,(device,group,seen)
   rows.append({'version':label,'device':device,'hostHz':hostHz,'group':group,'visiblePoses':sorted(seen),'changes':changes,'maxInstructions':c.max_instr})
importReport=json.loads((ROOT/'outputs/lumine-walk-fix-20261016/import.json').read_text(encoding='utf-8'))
from compact_assets import LuaRuntime,python_table
def data(folder):
 rt=LuaRuntime();rt.execute('__loaders={};'+(folder/'source/teaching/gf_lumine_training_data.lua').read_text(encoding='utf-8'));return python_table(rt.globals().__loaders['gf_lumine_training_data']())
old=data(ROOT/'outputs/tutorial-complete-v9-20261015');new=data(OUT)
for key,f in old['frames'].items():
 if not key.startswith(('walk_','back_')):assert new['frames'][key]==f,key
assert importReport['uniqueFrameMean']<1000
report={'clientSha256':hashlib.sha256((OUT/'genshin_fighter.lua').read_bytes()).hexdigest(),'results':rows,'old76NonWalkFramesUnchanged':True,'motherShaUnchanged':importReport['motherUnchangedSha256'],'uniqueFrameMean':importReport['uniqueFrameMean'],'peak':importReport['peak'],'scope':'mock presentation and candidate art; not aesthetic/native acceptance'}
(E/'walk-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps([{k:v for k,v in row.items()if k!='changes'}for row in rows]))
