"""Published legacy effect buffers can be reclaimed while hidden between rounds."""
from pathlib import Path
import sys,json,argparse
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mock_flow import Client,wait
ap=argparse.ArgumentParser();ap.add_argument('--before',type=Path,required=True);ap.add_argument('--after',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()

def case(source,key):
 c=Client(script=source,build=False,pools={'img':256,'txt':96,'btn':24},device='KeyboardAndMouse',canvas=(1600,900))
 c.rt.execute("local H=...;H.game.InstantiateClientUIControl=function(index,parent)return H.newControl('image','dynamic',parent,nil)end",c.H)
 c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c._to_lua({'chars':[key,key],'mode':'training','cpu':[False,False],'infinite':True})
 wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
 script="""local s=GF_APP().scene;local v=s.views[1];local f=v.f
f.state='burst';f.t=20;f.cinematicConfirmed=true
for i=1,40 do v:drawAnimatedFx() end
assert(v.animFxFront and v.animFxFront.key)
local prior=v.animFxFront
f.state='idle';v:drawAnimatedFx()
GF_REQUIRE('gf_gfx').reclaimDormant()
assert(prior.key==nil and prior.used==0)
f.state='burst';f.t=20;f.cinematicConfirmed=true
local ok,err=pcall(function()v:drawAnimatedFx()end)
if ok then
 for i=1,40 do v:drawAnimatedFx() end
 assert(v.animFxFront and v.animFxFront.used>0 and v.animFxFront.fxImage)
end
return ok,tostring(err)
"""
 ok,err=c.rt.execute('local _ENV=...;'+script,c.env)
 return {'key':key,'recovered':ok,'error':err if not ok else None}

rows=[]
for key in ['nahida','raidenshogun']:
 before=case(a.before,key);after=case(a.after,key)
 assert not before['recovered'] and "local 'shown'" in before['error'],before
 assert after['recovered'],after
 rows.append({'before':before,'after':after});print(json.dumps(rows[-1]),flush=True)
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps({'mockOnly':True,'realDeviceRegressionPending':True,'cases':rows},indent=2),encoding='utf-8')
