"""Complete publication, shared budget, and logic-clock hit feedback regression."""
from pathlib import Path
import sys,json,argparse
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mock_flow import RuntimeClient,wait,ROOT
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();RuntimeClient.source=a.source
def client():
 c=RuntimeClient(device='KeyboardAndMouse',canvas=(1600,900));c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c._to_lua({'chars':['furina','arlecchino'],'mode':'training','cpu':[False,False],'infinite':True,'time':999})
 wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans");c.run(1)
 c.lua("(function()local s=GF_APP().scene;s.sim.phase='fight';s.sim.freeze=0;for i,f in ipairs(s.sim.f)do s.sim:setState(f,'idle');f.x=i==1 and -40000 or 40000;f.hitstop=0;f.invul=9999 end;return true end)()")
 return c
c=client();peak=0;lag=[0,0];worst=[0,0]
for t in range(180):
 if t%30==0:c.lua("(function()local s=GF_APP().scene;for _,f in ipairs(s.sim.f)do s.sim:setState(f,'idle');s.sim:startMove(f,'heavy')end;return true end)()")
 c.step();b=c.lua("GF_REQUIRE('gf_gfx').lastBitmapBudget");assert b.used<=b.limit;peak=max(peak,b.used)
 c.lua("""(function()for _,v in ipairs(GF_APP().scene.views)do local b=v.front
 assert(b and not b.job,'partial body published');local img=v:image(b.key)
 assert(b.used==img.n,'body extent mismatch')
 for k=1,img.n do local o=k*5-5;local n=b.kids[k]
 assert(n.act and n.x==(img.ox or 0)-(img.ax or 0)+img.bytes[o+1]+img.bytes[o+3]/2,'body x mismatch')
 assert(n.y==(img.oy or 0)+(img.ay or 0)-img.bytes[o+2]-img.bytes[o+4]/2,'body y mismatch')
 assert(n.w==img.bytes[o+3]+(img.seam or .08) and n.h==img.bytes[o+4]+(img.seam or .08),'body size mismatch')
 end end;return true end)()""")
 for i in [1,2]:
  mismatch=c.lua(f'GF_APP().scene.views[{i}].front.key~=GF_APP().scene.views[{i}].want');lag[i-1]=lag[i-1]+1 if mismatch else 0;worst[i-1]=max(worst[i-1],lag[i-1])
 if t==18:c.render(a.out.parent/'attack-PC.png')
assert not list(c.H.err.values())
rates=[]
for hz in [60,30,15]:
 c=client();c.lua("(function()local s=GF_APP().scene;for _,v in ipairs(s.views)do v.updatePose=function()end;v:onHit({heavy=false})end;return true end)()")
 until=c.lua('GF_APP().scene.views[1].flashUntilTick');expired=None
 for n in range(12):
  c.step(1/hz);tick=c.lua('GF_APP().scene.sim.tick')
  if tick>=until:
   assert c.lua('GF_APP().scene.views[1].flashT==0 and not GF_APP().scene.views[1].flash.node.act and not GF_APP().scene.views[1].hitHalo.act')
   expired=tick;break
 assert expired is not None;rates.append({'callbackHz':hz,'deadlineTick':until,'firstSampleExpiredTick':expired})
c=client();c.lua("(function()for _,v in ipairs(GF_APP().scene.views)do v.updatePose=function()end;v.f.frozen=999;v:onHit({heavy=false})end;return true end)()")
for i in range(20):c.step()
assert c.lua("GF_APP().scene.views[1].flash.node.act and not GF_APP().scene.views[1].flash.job and GF_APP().scene.views[1].flash.used==GF_APP().scene.views[1].poseImg.n")
c.render(a.out.parent/'frozen-PC.png')
report={'scope':'PC mock only','publishedBodyGeometryExactCallbacks':180,'sharedRegisteredBitmapBudget':3200,'measuredBudgetPeak':peak,'maxConsecutiveCallbacksPoseBehind':worst,'feedbackLogicClock':rates,'completeFrozenOverlay':True,'nativeFPSVerified':False}
a.out.write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
