from pathlib import Path
import sys
sys.path[:0]=['runtime/tests','runtime/tools']
from mock_flow import RuntimeClient,wait
RuntimeClient.source=Path('outputs/tutorial-air-input-v22-20261017/genshin_fighter.lua').resolve()
c=RuntimeClient();c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':True,'lessonCourse':'low','seed':21})
wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
def probe(x):return c.lua('GF_APP().scene.'+x)
for i,key in enumerate(['J','K'],1):
 c.press('J');c.run(.15);c.key('S',True);c.press(key);c.key('S',False)
 wait(c,'GF_APP().scene.lesson.pending>0');print('done',i);c.press('J');c.run(.2)
c.press('J');c.run(.2)
c.lua("(function()GF_APP().scene.lesson.completeMenu.o.onPick('free');return true end)()")
c.run(1)
for jump in ['SPACE','W']:
 c.press(jump);c.run(.1);c.press('K');seen=[]
 for i in range(60):
  c.step();q=c.lua("(function()local s=GF_APP().scene;local a=s.sim.f[1];return {a.state,a.airMoveId or '',a.airT or -1,s.views[1].front.key or '',a.inNow,a.releaseMask or 0}end)()")
  row=[q[j]for j in range(1,7)]
  if not seen or row[3]!=seen[-1][3]:seen.append(row)
 print(jump,seen)
