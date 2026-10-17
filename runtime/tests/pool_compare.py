"""Controlled low-free condition: prove only proactive expansion is disabled."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
from performance import BenchClient
from mock_flow import wait,ROOT

def check(source):
    c=BenchClient(source);c.env.GF_FIRST_SCENE='test'
    wait(c,"GF_APP() and GF_APP().sceneName=='test' and not GF_APP().poolNext")
    result=c.lua("""(function()
local G=GF_REQUIRE('gf_gfx');G.requestImages(14000)
while not G.growImages(512) do end
local held={};while G.secondPoolStatus().freeFirst+G.secondPoolStatus().freeSecond>1900 do held[#held+1]=G.image(G.root) end
local before=G.secondPoolStatus();G.manageImagePool('fight',false)
local combat=G.secondPoolStatus();G.manageImagePool(nil,false)
local after=G.secondPoolStatus()
for _,n in ipairs(held)do G.release(n)end
return {before=before,combat=combat,after=after}
end)()""")
    return {k:dict(result[k].items()) for k in ['before','combat','after']}

if __name__=='__main__':
    baseline=ROOT.parent/'outputs/four-character-perf-gia-20261012_005019/gpt_20261012_005019_原神格斗_四角色帧率优化版.lua'
    comparison=ROOT/'verification/pool-comparison/genshin_fighter.lua'
    a,b=check(baseline),check(comparison)
    assert a['combat']['target']>a['before']['target'] and a['after']['total']>a['before']['total']
    assert b['after']['target']==b['before']['target']==14000 and b['after']['total']==14000
    report={'mockOnly':True,'thresholdFree':1900,'baseline':a,'comparison':b,'sceneLoadingPreserved':True,'proactiveGrowthDisabled':True}
    (ROOT/'verification/pool-comparison-check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
