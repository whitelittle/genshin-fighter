"""Authored effect pixels must reach the visible buffers and be freed on exit."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-wind-fx-v27-20261017'
sys.path[:0]=[str(ROOT/'runtime/tests'),str(ROOT/'runtime/tools')]
from mock_flow import RuntimeClient,wait
from teaching_backdash_render import CHECK
RuntimeClient.source=OUT/'genshin_fighter.lua'
CHECK_FX='''
local FXP=GF_REQUIRE('gf_character_assets').new(GF_REQUIRE('gf_wind_skill_fx_data'))
function checkWind(L)
 if L and L.windFront and L.windFront.node.act then
  checkBody({front=L.windFront,poseImg=FXP.image(L.windFront.key),slots=L.windPair});return L.windFront.key
 end
 return ''
end
'''
def run(device,hz):
 c=RuntimeClient(device=device,canvas=(1600,900));c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','seed':21})
 wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
 c.lua('(function()'+CHECK+CHECK_FX+'return true end)()');seen=set()
 for branch,keys in [('skill',['E']),('skillUp',['W','E']),('skillDown',['S','E'])]:
  c.lua("(function()local s=GF_APP().scene;local a,b=s.sim.f[1],s.sim.f[2];for _,p in ipairs({a,b})do s.sim:setState(p,'idle');p.y=0;p.vy=0;p.vx=0;p.hitstop=0;p.invul=0;p.skillCd=0;p.hp=p.maxhp end;a.x=-22000;b.x=22000;s.sim.proj={};return true end)()")
  c.run(.2)
  for k in keys:c.key(k,True)
  c.step(1/hz)
  for k in keys:c.key(k,False)
  for _ in range(100 if hz==60 else 50):
   c.step(1/hz)
   for name,expr in [('charge','GF_APP().scene.views[1].windL'),('projectile','GF_APP().scene.projL'),('impact','GF_APP().scene.views[1].windImpactL')]:
    key=c.lua('checkWind('+expr+')')
    if key:
     tag=branch+'-'+name+'-'+key
     if tag not in seen:
      seen.add(tag)
      if device=='KeyboardAndMouse':c.render(OUT/'verification'/f'{branch}-{name}-{key}.png')
 assert any('-impact-'in k for k in seen) and any('-projectile-blade_'in k for k in seen) and any('-projectile-orb_'in k for k in seen)
 c.lua('(function()GF_WIND_OLD=GF_APP().scene.views[1];GF_WIND_PROJ=GF_APP().scene.projL;GF_APP():travel("trainingcourses");return true end)()')
 wait(c,"GF_APP().sceneName=='trainingcourses' and not GF_APP().trans")
 assert c.lua('GF_WIND_OLD.windL==nil and GF_WIND_OLD.windImpactL==nil and GF_WIND_PROJ.windPair==nil')
 assert c.max_instr<1000000,c.max_instr
 return {'device':device,'hz':hz,'visibleExactEffectFrames':sorted(seen),'exitFreesEffectBitmaps':True,'maxInstructions':c.max_instr}
if __name__=='__main__':
 rows=[run(d,h)for d,h in [('KeyboardAndMouse',60),('Mobile',60),('Mobile',30)]]
 (OUT/'verification/authored-fx.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps([{k:v for k,v in r.items()if k!='visibleExactEffectFrames'}for r in rows]))
