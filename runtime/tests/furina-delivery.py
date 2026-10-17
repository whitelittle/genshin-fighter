"""Actual mobile mock scene: delivered E/Q/throw layers, scales and lifecycle."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mock_flow import RuntimeClient,wait,ROOT

def main():
    c=RuntimeClient(device='Mobile',canvas=(1600,900))
    c.env.GF_FIRST_SCENE='fight'
    c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['furina','raidenshogun']),
      'mode':'training','cpu':c.rt.table_from([False,False]),'rounds':2,'time':99,'infinite':True})
    wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
    c.run(1.2)
    receipts=[]
    for state,t in [('skill',18),('burst',24),('burst',78),('throw',30),('idle',0)]:
        c.lua(f"""(function()
local s=GF_APP().scene;local p,d=s.sim.f[1],s.sim.f[2]
s.sim.phase='fight';s.sim.freeze=1000;s.sim.events={{}};s.sim.proj={{}}
p.state='{state}';p.t={t};p.x=-20000;p.y=0;p.face=1;p.coat=0;p.airMove=nil;p.hitstop=0;p.frozen=0
p.move=p.kit.{'skill' if state=='skill' else 'burst'};p.moveId='{state}';p.cinematicConfirmed={'true' if state=='burst' else 'false'}
d.x=18000;d.y={10000 if state=='burst' and t>=56 else 0};d.state='{'thrown' if state=='throw' else 'hit' if state=='burst' else 'idle'}';d.face=-1;d.t={t};d.coat=0;d.hitstop=0;d.frozen=0
return true end)()""")
        c.run(.2)
        output=ROOT/f'verification/furina-mobile-{state}-{t}.png';c.render(output)
        scene=c.lua('GF_APP().scene');v=scene.views[1]
        if state=='skill':
            assert sum(bool(v.characterChannels[i].front) for i in range(1,5))==4
        if state=='burst' and t==24:assert scene.characterCutActive=='furina'
        if state=='idle':
            for i in range(1,5):
                for j in range(1,3):assert not v.characterChannels[i].slots[j].node.act
            assert all(not b.node.act for _,b in scene.characterCuts.items())
        receipts.append({'state':state,'tick':t,'image':output.relative_to(ROOT).as_posix(),'stats':c.stats()})
    (ROOT/'verification/furina-delivery.json').write_text(json.dumps({'mockOnly':True,'canonicalPage':'size-review.html','mobileLandscape':True,'checks':receipts},indent=2),encoding='utf-8')
    print(json.dumps({'mobileDeliveryLayers':True,'shots':len(receipts),'maximumControls':max(r['stats']['controls'] for r in receipts)}))
if __name__=='__main__':main()
