"""First-load release notice and separate tutorial/free-training routes."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent/'outputs/lumine-training-20261015'
sys.path.insert(0,str(ROOT/'tests'))
from mock_flow import RuntimeClient,wait
RuntimeClient.source=OUT/'candidate.lua'
results=[]
for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(1600,900)),('Mobile',(900,1600)),('Controller',(1600,900))]:
 c=RuntimeClient(device=device,canvas=canvas);c.env.GF_FIRST_SCENE='intro';c.env.GF_FIRST_ARGS=c.rt.table()
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().sceneName=='notice' and not GF_APP().trans")
 c.run(1);c.render(OUT/f'notice-{device}-{canvas[0]}.png')
 assert c.lua('#GF_APP().scene.items')==3
 assert c.lua("(function()local n=0;for _,e in ipairs(GF_APP().scene.items)do if e.title=='克洛琳德技能调整' then n=n+1 end;if string.find(e.title,'教学') or string.find(e.title,'公告') then return false end end;return n==1 end)()")
 assert c.lua("(function()for _,e in ipairs(GF_APP().scene.items)do if not e.confirmed or e.candidate then return false end end;return true end)()")
 c.key('J',True);c.step();c.key('J',False)
 wait(c,"GF_APP().scene and GF_APP().sceneName=='title' and not GF_APP().trans")
 c.lua("(function()GF_APP():travel('menu');return true end)()")
 wait(c,"GF_APP().scene and GF_APP().sceneName=='menu' and not GF_APP().trans")
 c.lua("(function()GF_APP().scene:pick('tutorial');return true end)()")
 wait(c,"GF_APP().scene and GF_APP().sceneName=='trainingcourses' and not GF_APP().trans")
 c.lua("(function()GF_APP().scene:pick('movement');return true end)()")
 wait(c,"GF_APP().scene and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
 assert c.lua("GF_APP().scene.args.tutorial and GF_APP().scene.lesson~=nil")
 c.lua("(function()GF_APP().scene:pausePick('quit');return true end)()")
 wait(c,"GF_APP().scene and GF_APP().sceneName=='menu' and not GF_APP().trans")
 c.lua("(function()GF_APP().scene:pick('training');return true end)()")
 wait(c,"GF_APP().scene and GF_APP().sceneName=='select' and not GF_APP().trans and not GF_APP().poolNext and GF_APP().scene.built==#GF_REQUIRE('gf_roster')")
 assert c.lua("GF_APP().scene.mode=='training'")
 c.lua("(function()local s=GF_APP().scene;s.cur={7,8};s:confirm(1);s:confirm(2);return true end)()")
 wait(c,"GF_APP().scene and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
 assert c.lua("GF_APP().scene.mode=='training' and GF_APP().scene.lesson==nil and GF_APP().scene.stage.key=='training'")
 c.run(.3);c.render(OUT/f'free-training-{device}-{canvas[0]}.png')
 c.lua("(function()GF_APP():travel('title');return true end)()")
 wait(c,"GF_APP().scene and GF_APP().sceneName=='title' and not GF_APP().trans")
 results.append({'device':device,'canvas':canvas,'noticeOncePerApp':True,'confirmedOnlyThreeEntries':True,'skillsGroupedOnceAndNoTutorialNoticeEntries':True,'tutorialToCourses':True,'trainingToSelectionAndFreeRoom':True,'lumineFreeRoomHasNoLesson':True});print(json.dumps(results[-1]),flush=True)
(OUT/'notice-checks.json').write_text(json.dumps({'mockOnly':True,'results':results},indent=2),encoding='utf-8')
