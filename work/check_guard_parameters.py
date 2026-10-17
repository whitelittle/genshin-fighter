import sys
from pathlib import Path
sys.path[:0]=['runtime/tests','runtime/tools']
from mock_flow import RuntimeClient
RuntimeClient.source=Path('outputs/tutorial-air-input-v22-20261017/genshin_fighter.lua').resolve();c=RuntimeClient()
q=c.lua("(function()local K=GF_REQUIRE('gf_kits');local R=GF_REQUIRE('gf_character_registry');local S=GF_REQUIRE('gf_sim_lumine_training');local s=S.new({chars={R.byKey.lumine,R.byKey.lawachurl},training=true,seed=21});s.phase='fight';s.freeze=0;local p=s.f[2];s:setState(p,'idle');s:startMove(p,'light1');local m=p.move;return {m.startup,m.active,m.recovery,s.f[1].kit.body.walk,s.f[1].kit.body.back,s.f[1].kit.body.dash}end)()")
print([q[i] for i in range(1,7)])

