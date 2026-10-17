from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'runtime/tests'))
from mock_flow import RuntimeClient,wait
O=R/'outputs/skill-feedback-20261014';RuntimeClient.source=O/'release/genshin_fighter.lua'
checks=[]
for device in ['KeyboardAndMouse','Mobile']:
 c=RuntimeClient(device=device,canvas=(1600,900))
 wait(c,"GF_APP() and GF_APP().sceneName=='title' and not GF_APP().trans and not GF_APP().poolNext")
 c.lua("(function()GF_APP():go('fight',{chars={'clorinde','clorinde'},mode='versus',cpu={false,false},stage='mondstadt',seed=21});return true end)()")
 wait(c,"GF_APP().sceneName=='fight' and GF_APP().scene.state=='run' and not GF_APP().trans")
 wait(c,"GF_APP().scene.sim.phase=='fight'")
 # Actual skill adapter, damage and event dispatch. Freeze only after each observation
 # to inspect the renderer independently of input and scene transitions.
 for kind in ['miss','hit','block','invul','down']:
  c.run(.4)
  c.lua(f"""(function()
   local sc=GF_APP().scene;local s=sc.sim;local p,d=s.f[1],s.f[2]
   s.freeze=0;p.x=-15000;d.x={'45000' if kind=='miss' else '0'};p.y=0;d.y=0;p.face=1;d.face=-1
   s:setState(p,'idle');s:setState(d,'{'down' if kind=='down' else 'idle'}');p.skillCd=0;p.invul=0;d.invul={30 if kind=='invul' else 0};d.hp=1000
   d.inNow={8 if kind=='block' else 0};sc.views[1].confirmedImpact=nil
   assert(s:startSkill(p));p.t=8;s.events={{}};s:skillUpdate(p);sc:events()
   local extras=GF_REQUIRE('gf_character_registry').provider('clorinde').extras(sc.views[1])
   assert((extras[3]~=nil)=={'true' if kind=='hit' else 'false'},'confirmed impact {kind}')
   assert({'d.hp<970' if kind=='hit' else 'd.hp>=970 and d.hp<1000' if kind=='block' else 'd.hp==1000'},'damage {kind}')
   s.freeze=100000;return true end)()""")
  c.run(.05);c.render(O/f'clorinde-{kind}-{device}.png')
  checks.append({'device':device,'skillCase':kind,'damageAndConfirmedImpact':True})
 for code in ['energy','cooldown','state','miss','block']:
  c.lua(f"(function()local sc=GF_APP().scene;sc.hud:skillFeedback({{p=1,code='{code}'}});sc.hud:skillFeedback({{p=2,code='{code}'}});return true end)()")
  c.step();c.render(O/f'feedback-{code}-{device}.png')
  assert c.lua("GF_APP().scene.hud.skillMessages[1].text~='' and GF_APP().scene.hud.skillMessages[2].text~=''")
  checks.append({'device':device,'feedbackCode':code,'twoFixedMessages':True})
 c.lua("(function()local h=GF_APP().scene.hud;h:skillFeedback({p=1,code='energy'});local old=h.skillMessages[1];h:skillFeedback({p=1,code='energy'});assert(old==h.skillMessages[1]);return true end)()")
 c.run(1);assert c.lua("GF_APP().t>=GF_APP().scene.hud.skillMessages[1].untilTime")
 # Real four-page scene, direct tab selection, separately from battle.
 c.lua("(function()GF_APP():go('howto',{});return true end)()")
 wait(c,"GF_APP().sceneName=='howto' and not GF_APP().trans")
 for page in range(1,5):
  c.lua(f"(function()GF_APP().input.menuQ={{'howto:{page}'}};return true end)()")
  c.run(.6);assert c.lua(f"GF_APP().scene.page=={page}");c.render(O/f'howto-{page}-{device}.png')
 errors=list(c.H.err.values())
 checks.append({'device':device,'fourPagesDirectTabs':True,'messageDedupAndExpiry':True,'errors':len(errors)})
 assert not errors,errors
(O/'visual-checks.json').write_text(json.dumps({'mockOnly':True,'checks':checks},ensure_ascii=False,indent=2),encoding='utf8')
print(len(checks),'visual/damage checks passed')
