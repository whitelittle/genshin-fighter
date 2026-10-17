"""Compare callback work on a fixed mobile mock; never report mock timings as native FPS."""
from pathlib import Path
import sys,json,statistics,time,argparse
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mock_flow import Client,ROOT,wait
class BenchClient(Client):
 def __init__(self,source):super().__init__(script=source,build=False,pools={'img':256,'txt':96,'btn':24},device='Mobile',canvas=(1600,900))
 def _build_tree(self):
  super()._build_tree();self.rt.execute("local H=...;H.game.InstantiateClientUIControl=function(index,parent)return H.newControl('image','dynamic',parent,nil) end",self.H)
def measure(source):
 result={}
 for key,other in [('raidenshogun','nahida'),('furina','kamisatoayaka'),('kamisatoayaka','furina')]:
  for label,state,duration in [('idle','idle',180),('walk','walk',180),('normal','attack',120),('E','skill',100),('Q','burst',180),('frozen','idle',120)]:
   c=BenchClient(source);c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from([key,other]),'mode':'training','cpu':c.rt.table_from([False,False]),'time':99,'rounds':2,'infinite':True,'seed':21})
   wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
   c.run(2);c.env.math.randomseed(73)
   c.lua(f"""(function()local s=GF_APP().scene;local p,d=s.sim.f[1],s.sim.f[2];s.sim.phase='fight';s.sim.freeze=0;p.x=-20000;d.x=10000;p.y=0;d.y=0;p.face=1;d.face=-1;p.energy=100;p.skillCd=0;p.hitstop=0;d.hitstop=0;p.frozen=0;d.frozen=0;p.coat=0;d.coat=0;s.sim.proj={{}};s.sim.events={{}};for _,f in ipairs(s.sim.f)do s.sim:setState(f,'idle');f.invul=0 end
{'s.sim:startBurst(p)' if state=='burst' else 's.sim:startSkill(p)' if state=='skill' else "s.sim:startMove(p,'heavy')" if state=='attack' else ''}
{'p.frozen=180' if label=='frozen' else ''}
return true end)()""")
   if label=='walk':c.key('D',True)
   instr=[];calls=[];bitmap=[];cols=[];elapsed=[];par=[]
   counts=lambda:c.lua("GF_REQUIRE('gf_gfx').N")
   last=dict(counts().items())
   for t in range(duration):
    c.max_instr=0;start=time.perf_counter();c.step();elapsed.append((time.perf_counter()-start)*1000)
    now=dict(counts().items());instr.append(c.max_instr);calls.append(c.calls[-1]);bitmap.append(now.get('bitmap',0)-last.get('bitmap',0));cols.append(now.get('col',0)-last.get('col',0));par.append(now.get('par',0)-last.get('par',0));last=now
   if label=='walk':c.key('D',False)
   result[key+'-'+label]={'instructionsMean':round(statistics.mean(instr)),'instructionsPeak':max(instr),'callsMean':round(statistics.mean(calls)),'callsPeak':max(calls),'bitmapWrites':sum(bitmap),'colorWrites':sum(cols),'parentWrites':sum(par),'mockMsMean':round(statistics.mean(elapsed),3),'mockMsPeak':round(max(elapsed),3),'controls':c.stats()['controls']}
 print(json.dumps(result,indent=2),flush=True);return result
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();data=measure(a.source);a.out.write_text(json.dumps({'scope':'fixed mobile mock only; not native FPS','cases':data},indent=2))
