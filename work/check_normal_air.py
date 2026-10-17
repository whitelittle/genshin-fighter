import sys,json
from pathlib import Path
sys.path[:0]=['runtime/tests','runtime/tools']
from mock_flow import RuntimeClient,wait
RuntimeClient.source=Path('outputs/tutorial-low-air-v21-20261017/genshin_fighter.lua').resolve()
for hz in [60,30]:
 for key in ['J','K']:
  c=RuntimeClient();c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','seed':21})
  wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
  c.press('SPACE');c.run(.1);c.key(key,True);rows=[]
  for i in range(65 if hz==60 else 33):
   c.step(1/hz)
   if i==1:c.key(key,False)
   q=c.lua("(function()local s=GF_APP().scene;local a=s.sim.f[1];local v=s.views[1];return {a.state,a.airMoveId or '',a.airT or -1,a.y,v.front.key or '',v.job and v.job.key or ''}end)()")
   rows.append([q[j] for j in range(1,7)])
  print(hz,key,json.dumps(rows))
