"""The briefing yields to the normal HUD; goals and device hints stay above play."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-polish-v10-20261016';E=OUT/'verification';E.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'runtime/tests'))
from mock_flow import RuntimeClient,wait
RuntimeClient.source=OUT/'genshin_fighter.lua'
rows=[]
for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(1600,900)),('Mobile',(900,1600)),('Controller',(1600,900))]:
 c=RuntimeClient(device=device,canvas=canvas);c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':True,'lessonCourse':'movement','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 def p(e):return c.lua('(function()local s=GF_APP().scene;return '+e+' end)()')
 assert p('s.lesson:isSpeaking()')
 c.render(E/f'briefing-{device}-{canvas[0]}.png')
 assert p('s.lesson.avatar.node.act and s.lesson.dialogue.node.act and not s.hud.root.act')
 c.lua('(function()GF_APP().scene:openPause();return true end)()');left=p('s.lesson.briefTicks');c.run(.3);assert p('s.lesson.briefTicks')==left;c.lua('(function()GF_APP().scene:closePause();return true end)()')
 wait(c,'not GF_APP().scene.lesson:isBriefing()');c.step()
 assert p('not s.lesson.avatar.node.act and not s.lesson.dialogue.node.act and s.hud.root.act')
 assert p('s.lesson.L.node.act')
 c.render(E/f'practice-hud-{device}-{canvas[0]}.png')
 # Native controls complete the target and bring Paimon back for feedback.
 if device=='Mobile':
  pos=c.lua('(function()local a=GF_APP();return {a.cw/2+(-a.W/2+230)*a.s,a.ch/2+(-a.H/2+200)*a.s,a.s}end)()');x,y,scale=pos[1],pos[2],pos[3]
  c.touch('down',x,y);c.touch('drag',x+80*scale,y)
 elif device=='Controller':c.H.game.GetControllerLeftStickAxis=lambda:(1,0)
 else:c.key('D',True)
 wait(c,'GF_APP().scene.lesson.pending>0')
 if device=='Mobile':c.touch('up',x+80*scale,y)
 elif device=='Controller':c.H.game.GetControllerLeftStickAxis=lambda:(0,0)
 else:c.key('D',False)
 c.step();assert p('s.lesson.avatar.node.act and s.lesson:isSpeaking() and not s.hud.root.act')
 c.render(E/f'feedback-{device}-{canvas[0]}.png')
 wait(c,'GF_APP().scene.lesson.index==2');assert p('s.lesson:isBriefing()')
 wait(c,'not GF_APP().scene.lesson:isBriefing()');c.step();assert p('s.hud.root.act and not s.lesson.avatar.node.act')
 rows.append({'device':device,'canvas':canvas,'briefingThenPracticeHud':True,'goalsAndHintsPersist':True,'feedbackThenNextBriefing':True,'pauseFreezesSpeech':True,'maxInstructions':c.max_instr});print(json.dumps(rows[-1]),flush=True)
(E/'dialogue-checks.json').write_text(json.dumps({'clientSha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'mockOnly':True,'results':rows},indent=2),encoding='utf-8')
