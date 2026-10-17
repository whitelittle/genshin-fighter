"""Cost ablations at 15/10 callback Hz, plus catch-up clock and zero decompression."""
from pathlib import Path
import sys,json,argparse,statistics
sys.path.insert(0,str(Path(__file__).resolve().parent))
from performance import BenchClient,wait
ap=argparse.ArgumentParser();ap.add_argument('--before',type=Path,required=True);ap.add_argument('--after',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
def sample(source,pair,mode,dt):
    c=BenchClient(source);c.env.GF_FIRST_SCENE='fight'
    c.env.GF_FIRST_ARGS=c._to_lua({'chars':pair,'mode':'training','cpu':[False,False],'infinite':True,'time':999})
    wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
    c.run(1)
    c.lua("(function()local s=GF_APP().scene;s.sim.phase='fight';s.sim.freeze=0;for i,f in ipairs(s.sim.f) do f.x=i==1 and -10000 or 10000;f.hitstop=0;f.frozen=0;s.sim:setState(f,'idle')end;return true end)()")
    initial=c.lua('GF_APP().scene.sim.tick');calls=[];instr=[];cols=[]
    for i in range(round(6/dt)):
        if mode=='hits' and i%6==0:
            c.lua("(function()local s=GF_APP().scene;for _,v in ipairs(s.views)do v:onHit({heavy=false})end;return true end)()")
        if mode=='skill' and i%24==0:
            c.lua("(function()local s=GF_APP().scene;for _,f in ipairs(s.sim.f)do s.sim:setState(f,'idle');f.skillCd=0;assert(s.sim:startSkill(f))end;return true end)()")
        c.max_instr=0;before=c.lua("GF_REQUIRE('gf_gfx').N.col");c.step(dt)
        calls.append(c.calls[-1]);instr.append(c.max_instr);cols.append(c.lua("GF_REQUIRE('gf_gfx').N.col")-before)
    ticks=c.lua('GF_APP().scene.sim.tick')-initial
    if source==a.after:
        assert abs(ticks-360)<=1,(mode,dt,ticks)
        assert c.lua("GF_REQUIRE('gf_util').compressionStats.blocks")==0
        assert not c.heavy,c.heavy
    return {'callsMean':round(statistics.mean(calls)),'callsPeak':max(calls),'colorWrites':sum(cols),'instructionsPeak':max(instr),'simTicksIn6Seconds':ticks,'residentImages':c.lua('GF_SECOND_POOL_STATUS().total'),'LZ4Blocks':c.lua("GF_REQUIRE('gf_util').compressionStats.blocks")}
rows=[]
for pair in [['furina','arlecchino'],['arlecchino','nahida'],['kamisatoayaka','nahida']]:
    for mode in ['idle','hits','skill']:
        dt=.1
        row={'pair':pair,'scenario':mode,'callbackHz':10,'before':sample(a.before,pair,mode,dt),'after':sample(a.after,pair,mode,dt)}
        rows.append(row);print(row,flush=True)
a.out.write_text(json.dumps({'mockOnly':True,'nativeFPSNotMeasured':True,'cases':rows},indent=2),encoding='utf-8')
