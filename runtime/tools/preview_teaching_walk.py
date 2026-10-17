"""Local teaching preview for the isolated walk candidate."""
from pathlib import Path
import hashlib,sys,json
from collections import deque
sys.path.insert(0,str(Path(__file__).resolve().parent))
import preview
class WalkClient(preview.RuntimeClient):
 source=preview.REPO/'outputs/tutorial-wind-fx-v27-20261017/genshin_fighter.lua'
 def step(self,dt=1/60):
  super().step(dt)
  if not hasattr(self,'inputTrace'):self.inputTrace=deque(maxlen=900)
  state=self.lua("""(function()
   local a=GF_APP();local s=a and a.scene;if not s or not s.sim or not s.views then return nil end
   local p=s.sim.f[1];local v=s.views[1];if not p or not v then return nil end
   local l=s.lesson;local pad=a.input:pad(1)
   return {frame=a.frame,tick=s.sim.tick,course=l and l.course or 'free',index=l and l.index or 0,
    speaking=l and l:isSpeaking() or false,completeMenu=l and l.completeMenu~=nil or false,
    pending=l and l.pending or 0,state=p.state,t=p.t,y=p.y,hits=p.stats.hits,
    hp=s.sim.f[2].hp,input=p.inNow,pressed=p.inPressed,release=p.releaseMask,
    held=pad.held,touch=pad.touch,airActive=p.airMove~=nil,air=p.airMoveId,
    move=p.moveId,airT=p.airT,want=v.want,shown=v.front and v.front.key}
  end)()""")
  if state:
   row=dict(state.items());self.inputTrace.append(row)
   if not hasattr(self,'inputTransitions'):self.inputTransitions=deque(maxlen=240);self.lastInputSignature=None
   signature=tuple(row.get(k)for k in ['course','index','speaking','state','airActive','move','air','want','shown','input','hits'])
   if signature!=self.lastInputSignature:
    self.inputTransitions.append(row);self.lastInputSignature=signature
 def stats(self):
  r=super().stats();r['clientSha256']=hashlib.sha256(self.source.read_bytes()).hexdigest()
  trace=list(getattr(self,'inputTrace',[]))
  if trace:
   r['teachingState']=trace[-1]
   out=self.source.parent/'verification/live-input-trace.json'
   out.write_text(json.dumps({'clientSha256':r['clientSha256'],'transitions':list(self.inputTransitions),'samples':trace},ensure_ascii=False),encoding='utf-8')
  return r
preview.preview.Client=WalkClient
if __name__=='__main__':
 if '--scene' not in sys.argv:sys.argv.extend(['--scene','trainingcourses'])
 if '--canvas' not in sys.argv:sys.argv.extend(['--canvas','1600x900'])
 preview.preview.main()
