from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/clorinde-sword-tip-20261014'
sys.path.insert(0,str(R/'runtime/tests'))
from mock_flow import RuntimeClient,wait
RuntimeClient.source=O/'release/genshin_fighter.lua';rows=[]
for device in ['KeyboardAndMouse','Mobile']:
 c=RuntimeClient(device=device,canvas=(1600,900))
 wait(c,"GF_APP() and GF_APP().sceneName=='title' and not GF_APP().trans and not GF_APP().poolNext")
 c.lua("(function()GF_APP():go('fight',{chars={'clorinde','clorinde'},mode='versus',cpu={false,false},stage='mondstadt',seed=21});return true end)()")
 wait(c,"GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
 wait(c,"GF_APP().scene.sim.phase=='fight'")
 markers=json.loads((O/'blade-marker-audit.json').read_text(encoding='utf8'))['markers']
 for m in markers:
  for face in [1,-1]:
   move=m['move'];t=m['start']
   c.lua(f"""(function()
    local sc=GF_APP().scene;local s=sc.sim;local p,d=s.f[1],s.f[2]
    p.skillCd=0;p.y=0;p.x=-15000;p.face={face};d.x=60000;d.y=0;p.connected=false;p.airMove=nil;p.airMoveId=nil;p.airT=0
    sc.views[1].confirmedImpact=nil;s:setState(d,'idle');s:setState(p,'{'air' if move=='airHeavy' else 'idle'}')
    {'assert(s:startSkill(p))' if move=='skill' else f"assert(s:startMove(p,'{move}'))"}
    {'p.airT='+str(t+1) if move=='airHeavy' else 'p.t='+str(t)}
    s.freeze=100000;return true end)()""")
   c.run(.4)
   assert c.lua(f"GF_APP().scene.views[1].front.key=='{m['pose']}'"),(device,m['pose'],c.lua('GF_APP().scene.views[1].front.key'))
   assert c.lua("GF_APP().scene.views[1].characterChannels[1].front.node.act")
   c.render(O/f'{m["pose"]}-face{face}-{device}.png')
   rows.append({'device':device,'pose':m['pose'],'face':face,'actualBodyAndSwordPublished':True})
 assert not list(c.H.err.values())
(O/'blade-render-checks.json').write_text(json.dumps({'mockOnly':True,'sourceSha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'checks':rows},indent=2),encoding='utf8')
print(len(rows),'blade body/effect publication checks passed')
