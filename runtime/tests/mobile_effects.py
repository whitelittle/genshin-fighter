"""Mobile lightweight feedback and desktop artwork fallback visual checks."""
from pathlib import Path
import sys,argparse,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mock_flow import RuntimeClient,wait
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();RuntimeClient.source=a.source
rows=[]
for device in ['Mobile','KeyboardAndMouse']:
    c=RuntimeClient(device=device,canvas=(1950,900));c.env.GF_FIRST_SCENE='fight'
    c.env.GF_FIRST_ARGS=c._to_lua({'chars':['nahida','arlecchino'],'mode':'training','cpu':[False,False],'infinite':True})
    wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
    c.lua("(function()local s=GF_APP().scene;s.sim.phase='fight';s.sim.freeze=10000;local p=s.sim.f[1];p.x=-12000;p.y=0;p.state='skill';p.t=11;p.move=p.kit.skill;p.captureHitT=nil;p.castX=p.x;p.castY=19000;p.castFace=1;return true end)()")
    c.run(.3);c.render(a.out/f'viewfinder-{device}.png')
    if device=='Mobile':
        assert c.lua('GF_APP().scene.views[1].captureL.n==11 and GF_APP().scene.views[1].captureBmp.used==0')
        assert c.lua('#GF_APP().scene.views[1].flash.kids==0')
    else:assert c.lua('GF_APP().scene.views[1].captureBmp.used==796')
    c.lua("(function()GF_APP().scene.views[2]:onHit({heavy=false});return true end)()");c.step();c.render(a.out/f'hit-feedback-{device}.png')
    if device=='Mobile':assert c.lua('GF_APP().scene.views[2].hitHalo.act and #GF_APP().scene.views[2].flash.kids==0')
    else:assert c.lua('GF_APP().scene.views[2].flash.node.act')
    assert not c.heavy and not list(c.H.err.values())
    rows.append({'device':device,'lightweightMobileAndOriginalDesktop':True,'maxInstructions':c.max_instr})
(a.out/'mobile-effects.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(rows)
