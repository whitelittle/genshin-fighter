import sys
from pathlib import Path
sys.path.insert(0,'runtime/tests')
from mock_flow import RuntimeClient,wait
RuntimeClient.source=Path('outputs/pc-attack-budget-20261014/shared-budget/genshin_fighter.lua')
c=RuntimeClient(device='KeyboardAndMouse');c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c._to_lua({'chars':['clorinde','clorinde'],'mode':'training','cpu':[False,False],'infinite':True,'time':999})
wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
c.run(1)
print('flag',c.lua('GF_APP().scene.views[1].slots[1].budgeted'))
print('budget',dict(c.lua("GF_REQUIRE('gf_gfx').lastBitmapBudget").items()))
c.lua("(function()local s=GF_APP().scene;for _,f in ipairs(s.sim.f)do s.sim.phase='fight';s.sim.freeze=0;s.sim:setState(f,'idle');s.sim:startMove(f,'heavy')end;return true end)()")
for i in range(20):
 n=c.lua("GF_REQUIRE('gf_gfx').N.bitmap");c.step();b=c.lua("GF_REQUIRE('gf_gfx').lastBitmapBudget");print(i,c.lua("GF_REQUIRE('gf_gfx').N.bitmap")-n,b.used,b.left,c.lua('GF_APP().scene.views[1].slots[1].budgeted'))
