"""Exercise lesson completion through real input and confirmed hits, not UI clicks."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent/'outputs/lumine-training-20261015'
sys.path.insert(0,str(ROOT/'tests'))
from mock_flow import RuntimeClient,wait
RuntimeClient.source=OUT/'candidate.lua'
results=[]
for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(1600,900)),('Mobile',(900,1600))]:
 c=RuntimeClient(device=device,canvas=canvas)
 c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':True,'seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight'")
 c.run(.2);c.render(OUT/f'lesson-start-{device}-{canvas[0]}.png')
 def idx():return c.lua('GF_APP().scene.lesson.index')
 def pending():return c.lua('GF_APP().scene.lesson.pending')
 def act(key):
  c.key(key,True)
  for _ in range(600):
   c.step()
   if pending()>0:break
  c.key(key,False);c.step()
  assert pending()>0,(device,idx(),key)
 def next_step(n):wait(c,f'GF_APP().scene.lesson.index=={n} and not GF_APP().scene.lesson:isBriefing()')
 assert idx()==1
 # Earlier damage must not auto-complete the later attack objective.
 c.lua('(function()GF_APP().scene.sim.f[1].stats.hits=3;return true end)()')
 act('D');old=c.lua('GF_APP().scene.lesson.line')
 c.lua('(function()GF_APP().scene:openPause();return true end)()');p=pending();c.run(.5);assert pending()==p
 c.lua('(function()GF_APP().scene:closePause();return true end)()');next_step(2);assert c.lua('GF_APP().scene.lesson.line')!=old
 act('A');next_step(3)
 # One actual jump, then release so it can land without auto-jumping again.
 c.key('W',True);c.run(.12);c.key('W',False)
 wait(c,'GF_APP().scene.lesson.pending>0');next_step(4)
 act('U');next_step(5)
 act('D');next_step(6);assert pending()==0
 # Deliberate air swing far away cannot advance a hit lesson.
 c.lua("(function()local s=GF_APP().scene.sim;s.f[1].x=-50000;s.f[2].x=50000;s:setState(s.f[1],'idle');return true end)()")
 c.key('J',True);c.run(.6);c.key('J',False);c.step();assert idx()==6 and pending()==0
 c.lua("(function()local s=GF_APP().scene.sim;s.f[1].x=-9000;s.f[2].x=9000;s.f[1].vx=0;s.f[2].vx=0;s:setState(s.f[1],'idle');return true end)()")
 act('J');c.render(OUT/f'lesson-hit-{device}-{canvas[0]}.png');next_step(7)
 c.run(.3);c.render(OUT/f'lesson-finished-{device}-{canvas[0]}.png')
 assert c.lua('GF_APP().scene.sim.f[1].stats.hits')>3
 c.lua("(function()GF_APP().scene:pausePick('restart');return true end)()")
 wait(c,"GF_APP().scene and GF_APP().scene.state=='run' and not GF_APP().trans")
 assert idx()==1 and pending()==0
 results.append({'device':device,'canvas':canvas,'sixObjectivesInOrder':True,'pauseStopsAdvance':True,'oldHitAndWhiffCannotComplete':True,'automaticDialogue':True,'restartResets':True,'stats':c.stats()});print(json.dumps(results[-1]),flush=True)
(OUT/'lesson-checks.json').write_text(json.dumps({'mockOnly':True,'results':results},indent=2),encoding='utf-8')
