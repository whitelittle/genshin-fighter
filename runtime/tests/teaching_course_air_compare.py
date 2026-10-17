"""Compare identical close-range airborne inputs in low and air courses."""
from pathlib import Path
import sys,json,argparse
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runtime/tests'),str(ROOT/'runtime/tools')]
from mock_flow import RuntimeClient,wait
from teaching_backdash_render import CHECK
def run(out,course,attack,delay):
 RuntimeClient.source=out/'genshin_fighter.lua'
 c=RuntimeClient(device='KeyboardAndMouse',canvas=(1600,900));c.env.GF_FIRST_SCENE='fight'
 c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','tutorial':True,'lessonCourse':course,'seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 c.press('J');c.run(.2);c.lua('(function()'+CHECK+'return true end)()')
 c.press('SPACE',frames=1)
 for _ in range(delay):c.step()
 c.press(attack,frames=1);rows=[]
 for _ in range(80):
  c.step();c.lua('checkBody(GF_APP().scene.views[1])')
  row=c.lua("(function()local s=GF_APP().scene;local a=s.sim.f[1];return {tick=s.sim.tick,state=a.state,move=a.moveId,air=a.airMoveId,active=a.airMove~=nil,t=a.airT,y=a.y,hits=a.stats.hits,want=s.views[1].want,shown=s.views[1].front.key,pending=s.lesson.pending}end)()")
  rows.append(dict(row.items()))
 return {'course':course,'attack':attack,'delay':delay,'rows':rows}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--target',default='outputs/tutorial-short-press-v24-20261017');a=ap.parse_args();out=ROOT/a.target
 rows=[run(out,g,k,d)for g in ['low','air']for k in ['J','K']for d in [0,6,15]]
 (out/'verification/course-air-compare.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
 for r in rows:print(r['course'],r['attack'],r['delay'],'hits',max(x['hits']for x in r['rows']),'seen',list(dict.fromkeys(x['shown']for x in r['rows'])))
