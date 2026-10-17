from pathlib import Path
import sys,json,statistics
repo=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(repo/'runtime/tests'))
from mock_flow import Client,wait

def sample(pair,scenario,dt):
 c=Client(script=repo/'outputs/mobile-performance-20261013/integrated/genshin_fighter.lua',build=False,pools={'img':256,'txt':96,'btn':24},device='KeyboardAndMouse',canvas=(1600,900))
 c.rt.execute("local H=...;H.game.InstantiateClientUIControl=function(index,parent)return H.newControl('image','dynamic',parent,nil)end",c.H)
 c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c._to_lua({'chars':pair,'mode':'training','cpu':[False,False],'infinite':True,'time':999})
 wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
 c.run(1)
 c.lua("(function()local s=GF_APP().scene;s.sim.phase='fight';s.sim.freeze=0;for i,f in ipairs(s.sim.f)do f.x=i==1 and -10000 or 10000;f.hitstop=0;s.sim:setState(f,'idle')end;return true end)()")
 if scenario=='static-body':c.lua("(function()for _,v in ipairs(GF_APP().scene.views)do v.updatePose=function()end end;return true end)()")
 if scenario=='walk':c.key('D',True)
 calls=[];instructions=[];last=dict(c.lua("GF_REQUIRE('gf_gfx').N").items());deltas={k:[] for k in ['bitmap','size','col','par','pos','vis']}
 for i in range(round(3/dt)):
  if scenario=='hits' and i%6==0:c.lua("(function()for _,v in ipairs(GF_APP().scene.views)do v:onHit({heavy=false})end;return true end)()")
  c.max_instr=0;c.step(dt);calls.append(c.calls[-1]);instructions.append(c.max_instr)
  current=dict(c.lua("GF_REQUIRE('gf_gfx').N").items())
  for k in deltas:deltas[k].append(current.get(k,0)-last.get(k,0))
  last=current
 result={'pair':pair,'scenario':scenario,'callbackHz':round(1/dt),'callsMean':round(statistics.mean(calls)),'callsPeak':max(calls),'instructionsPeak':max(instructions),'residentImages':c.lua('GF_SECOND_POOL_STATUS().total'),'bodyPeaks':[c.lua(f'GF_APP().scene.views[{i}].bodyCapacity') for i in (1,2)],'frontRectangles':[c.lua(f'GF_APP().scene.views[{i}].front.used') for i in (1,2)],'writeMeans':{k:round(statistics.mean(v)) for k,v in deltas.items()},'writePeaks':{k:max(v) for k,v in deltas.items()},'errors':list(c.H.err.values())}
 print(json.dumps(result),flush=True)
 return result

rows=[]
for pair in [['clorinde','clorinde'],['raidenshogun','nahida']]:
 for scenario in ['idle','static-body','walk','hits']:
  rows.append(sample(pair,scenario,1/60))
rows.append(sample(['clorinde','clorinde'],'idle',1/15))
out=repo/'outputs/pc-load-audit-20261013';out.mkdir(exist_ok=True)
(out/'mock-cost.json').write_text(json.dumps({'mockOnly':True,'nativeFPSMeasured':False,'rows':rows},indent=2),encoding='utf-8')
