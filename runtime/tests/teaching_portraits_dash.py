from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-polish-v12-20261016';E=OUT/'verification'
sys.path.insert(0,str(ROOT/'runtime/tests'));sys.path.insert(0,str(ROOT/'runtime/tools'))
from mock_flow import RuntimeClient,wait
from compact_assets import python_table
RuntimeClient.source=OUT/'genshin_fighter.lua'
rows=[]
for device,canvas in [('KeyboardAndMouse',(1600,900)),('Mobile',(900,1600))]:
 c=RuntimeClient(device=device,canvas=canvas);c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 result=python_table(c.lua("(function()local a=GF_REQUIRE('gf_art');assert(a.round('lumine').n==344 and a.round('lawachurl').n==448);return {standardIcons=true}end)()"))
 c.render(E/f'standard-portraits-{device}.png');rows.append({'device':device,**result})
 # Compare new isolated dash with the original Base implementation on the same role.
 rules=python_table(c.lua("""(function()
 local S=GF_REQUIRE('gf_sim_lumine_training');local R=GF_REQUIRE('gf_character_registry');local Base=GF_REQUIRE('gf_sim')
 local function run(sign,back,old,wall)
  local s=S.new({chars={R.byKey.lumine,R.byKey.lawachurl},training=true,seed=21});s.phase='fight';s.freeze=0
  local p,d=s.f[1],s.f[2];s:setState(p,'idle');s:setState(d,'idle');p.x=sign*(-40000);d.x=sign*40000;p.face=sign;d.face=-sign
  if wall then p.x=sign*(Base.WALL-5000);d.x=p.x-sign*70000;p.face=sign;d.face=-sign end
  if old then s.neutral=Base.neutral end
  local x=p.x;local frames=0;s:step(back and (256|(sign==1 and 4 or 8)) or 256,0)
  repeat s:step(0,0);frames=frames+1 until (p.state~='dash' and p.state~='backdash') or frames>100
  assert(math.abs(p.x)<=Base.WALL)
  return math.abs(p.x-x),frames,s
 end
 local old,frames=run(1,false,true);local new,n=run(1,false,false);assert(new>old*2.15 and new<old*2.25 and n==frames,old..' '..new..' '..frames..' '..n)
 for _,side in ipairs({-1,1})do local b=run(side,true,true);local a=run(side,true,false);assert(a==b);run(side,false,false,true)end
 local _,_,s=run(1,false,false);local copy=S.copy(s);for i=1,400 do local m=i%90==0 and 256 or 0;s:step(m,0);copy:step(m,0);assert(s:hash()==copy:hash())end
 return {oldDistance=old/100,newDistance=new/100,durationUnchanged=true,backdashUnchangedBothSides=true,wallsAndReplay=true}
 end)()"""));rows[-1]['dash']=rules;print(json.dumps(rows[-1]),flush=True)
(E/'portraits-dash-checks.json').write_text(json.dumps({'clientSha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'mockOnly':True,'results':rows},indent=2),encoding='utf-8')
