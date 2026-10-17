from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/clorinde-ballistics-20261014'
sys.path.insert(0,str(R/'runtime/tests'))
from mock_flow import RuntimeClient,wait
RuntimeClient.source=O/'release/genshin_fighter.lua';rows=[]
for device in ['KeyboardAndMouse','Mobile']:
 c=RuntimeClient(device=device,canvas=(1600,900))
 wait(c,"GF_APP() and GF_APP().sceneName=='title' and not GF_APP().trans and not GF_APP().poolNext")
 c.lua("(function()GF_APP():go('fight',{chars={'clorinde','clorinde'},mode='versus',cpu={false,false},stage='mondstadt',seed=21});return true end)()")
 wait(c,"GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
 wait(c,"GF_APP().scene.sim.phase=='fight'")
 for id in ['light2','heavy','airLight','skill']:
  for face in [1,-1]:
   for distance in [450,650,850]:
    c.run(.4)
    result=c.lua(f"""(function()
     local sc=GF_APP().scene;local s=sc.sim;local p,d=s.f[1],s.f[2]
     s.freeze=0;p.x={-distance*50 if face==1 else distance*50};d.x=p.x+{face*distance*100};p.y=0;d.y=0;p.face={face};d.face={-face}
     p.skillCd=0;p.invul=0;d.invul=0;d.hp=1000;d.inNow=0;sc.views[1].confirmedImpact=nil
     s:setState(d,'idle');s:setState(p,'{'air' if id=='airLight' else 'idle'}')
     {'assert(s:startSkill(p))' if id=='skill' else f"assert(s:startMove(p,'{id}'))"}
     local startup={'8' if id=='skill' else f"p.{'airMove' if id=='airLight' else 'move'}.startup"}
     local tick=nil
     for age=0,7 do
      s.events={{}}
      {'p.t=startup+age;s:skillUpdate(p)' if id=='skill' else 'p.airT=startup+age;s:airAttackUpdate(p)' if id=='airLight' else 'p.t=startup+age;s:attackUpdate(p)'}
      sc:events()
      if d.hp<1000 then tick=startup+age;break end
     end
     assert((tick~=nil)=={'true' if distance<850 else 'false'},'shot contact {id} {face} {distance}')
     s.freeze=100000;return {{hit=tick~=nil,tick=tick,hp=d.hp}} end)()""")
    c.run(.05)
    c.render(O/f'{id}-face{face}-distance{distance}-{device}.png')
    rows.append({'device':device,'move':id,'face':face,'distance':distance,'hit':bool(result.hit),'tick':result.tick,'hp':result.hp})
 assert not list(c.H.err.values())
(O/'shot-render-checks.json').write_text(json.dumps({'mockOnly':True,'sourceSha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'checks':rows},indent=2),encoding='utf8')
print(len(rows),'PC / phone landscape shot contact render checks passed')
