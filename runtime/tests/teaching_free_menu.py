"""Click a disposed completion menu area again, as in the reported crash."""
from pathlib import Path
import sys,argparse,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'runtime/tests'))
from mock_flow import RuntimeClient,wait

def run(device,canvas,out):
 RuntimeClient.source=out/'genshin_fighter.lua'
 c=RuntimeClient(device=device,canvas=canvas)
 c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':True,'lessonCourse':'movement','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 c.lua('(function()GF_APP().scene.lesson:enter(6);return true end)()');c.step();c.press('J');c.step()
 pos=c.lua('(function()local a=GF_APP();local m=a.scene.lesson.completeMenu;return {a.cw/2+m.o.x*a.s,a.ch/2+m:rowY(3)*a.s}end)()')
 x,y=pos[1],pos[2]
 def click():c.touch('down',x,y);c.step();c.touch('up',x,y);c.step()
 click()
 assert c.lua('GF_APP().scene.lesson.completeMenu==nil')
 for _ in range(5):click()
 c.press('P');c.run(.15);c.press('P');c.run(.15)
 c.press('U');c.run(.4)
 assert c.lua('GF_APP().scene.lesson.completeMenu==nil and not GF_APP().scene.paused')
 assert c.max_instr<1000000,c.max_instr
 return {'device':device,'canvas':canvas,'repeatedDisposedMenuClicks':True,'pauseResumeAndDash':True,'maxInstructions':c.max_instr}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--baseline',action='store_true');ap.add_argument('--target');args=ap.parse_args()
 out=ROOT/('outputs/tutorial-render-v16-20261017' if args.baseline else 'outputs/tutorial-unified-v17-20261017')
 if args.target:out=ROOT/args.target
 rows=[run(d,s,out) for d,s in [('KeyboardAndMouse',(1600,900)),('Mobile',(1600,900)),('Mobile',(900,1600)),('Controller',(1600,900))]]
 result={'clientSha256':hashlib.sha256((out/'genshin_fighter.lua').read_bytes()).hexdigest(),'results':rows,'offlineOnly':True}
 (out/'verification/free-menu.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps(result))
