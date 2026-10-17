"""Independent course shell, lesson completion, catalogue and return flow."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent/'outputs/lumine-training-20261015'
sys.path.insert(0,str(ROOT/'tests'))
from mock_flow import RuntimeClient,wait
RuntimeClient.source=OUT/'candidate.lua'
results=[]
for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(1600,900)),('Mobile',(900,1600)),('Controller',(1600,900))]:
 c=RuntimeClient(device=device,canvas=canvas);c.env.GF_FIRST_SCENE='trainingcourses'
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().sceneName=='trainingcourses'")
 c.run(1);c.render(OUT/f'courses-{device}-{canvas[0]}.png')
 def pick(id):c.lua(f"(function()GF_APP().scene:pick('{id}');return true end)()")
 pick('elements');assert c.lua("GF_APP().scene.page=='elements' and #GF_APP().scene.items==8")
 assert c.lua("(function()for _,e in ipairs(GF_REQUIRE('gf_training_courses').elements)do if not e.available then return false end end;return true end)()")
 pick('back')
 assert c.lua("#GF_APP().scene.items==12")
 pick('movement')
 wait(c,"GF_APP().scene and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 assert c.lua("GF_APP().scene.lesson.course=='movement' and #GF_APP().scene.lesson.lessons==5")
 c.run(.3);c.render(OUT/f'course-movement-{device}-{canvas[0]}.png')
 # Three real-input fundamentals are covered exhaustively in lumine_lesson;
 # this check covers the new actual backstep target and end-of-course branching.
 c.lua('(function()GF_APP().scene.lesson:enter(5);return true end)()')
 wait(c,'not GF_APP().scene.lesson:isBriefing()')
 c.key('A',True);c.step();c.key('U',True)
 for _ in range(40):
  c.step()
  if c.lua('GF_APP().scene.lesson.pending>0'):break
 c.key('A',False);c.key('U',False);c.step()
 assert c.lua('GF_APP().scene.lesson.pending>0')
 wait(c,'GF_APP().scene.lesson.completeMenu~=nil');assert c.lua('GF_APP().trainingCompleted.movement')
 c.run(.8);c.render(OUT/f'course-completed-{device}-{canvas[0]}.png')
 c.lua("(function()local m=GF_APP().scene.lesson.completeMenu;m.o.onPick('courses');return true end)()")
 wait(c,"GF_APP().scene and GF_APP().sceneName=='trainingcourses' and not GF_APP().trans")
 pick('attack');wait(c,"GF_APP().scene and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
 assert c.lua("GF_APP().scene.lesson.course=='attack' and #GF_APP().scene.lesson.lessons==5")
 c.lua("(function()GF_APP().scene.lesson:enter(6);GF_APP().scene.lesson.completeMenu.o.onPick('free');return true end)()")
 assert c.lua('GF_APP().scene.lesson.completeMenu==nil')
 tick=c.lua('GF_APP().scene.sim.tick');c.run(.3);assert c.lua('GF_APP().scene.sim.tick')>tick
 c.lua("(function()GF_APP().scene:pausePick('courses');return true end)()")
 wait(c,"GF_APP().scene and GF_APP().sceneName=='trainingcourses' and not GF_APP().trans")
 results.append({'device':device,'canvas':canvas,'elevenCourseCategories':True,'sevenElementPages':True,'allCourseEntriesAvailable':True,'realBackstep':True,'completeReturnReplayFreePractice':True,'stats':c.stats()});print(json.dumps(results[-1]),flush=True)
(OUT/'course-checks.json').write_text(json.dumps({'mockOnly':True,'results':results},indent=2),encoding='utf-8')
