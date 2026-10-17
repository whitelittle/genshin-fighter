"""Authored wind effects and a deliberately bounded juggle extension prototype."""
from pathlib import Path
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'outputs/tutorial-wind-combo-v26-20261017';OUT=ROOT/'outputs/tutorial-wind-fx-v27-20261017'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
 shutil.copytree(BASE/'source',OUT/'source',dirs_exist_ok=True);(OUT/'verification').mkdir(exist_ok=True)
 def edit(rel,before,after):
  p=OUT/'source'/rel;s=p.read_text(encoding='utf-8');assert s.count(before)==1,(rel,before);p.write_text(s.replace(before,after),encoding='utf-8')
 edit('teaching/gf_lumine_training_rules.lua',"cancel={'jump'}","cancel={'jump','skill'}")
 edit('teaching/gf_lumine_training_rules.lua',"cancel={'light3','crouchHeavy','skill'}","cancel={'light3','crouchHeavy','skill','jump'}")
 edit('teaching/gf_sim_lumine_training.lua',"if a.key=='lumine' and actualMove=='crouchHeavy' then a.trainingLaunchHit=result=='hit' end", "if a.key=='lumine' and (actualMove=='crouchHeavy' or actualMove=='light2') then a.trainingLaunchHit=result=='hit' and d.state=='airhit' end")
 edit('teaching/gf_sim_lumine_training.lua',"if p.key=='lumine' and p.moveId=='crouchHeavy' and p.trainingLaunchHit and p.connected and p.t<=m.startup+m.active+8 and p.inPressed&1~=0", "if p.key=='lumine' and (p.moveId=='crouchHeavy' or p.moveId=='light2') and p.trainingLaunchHit and p.connected and p.t<=m.startup+m.active+8 and p.inPressed&1~=0")
 edit('teaching/gf_sim_lumine_training.lua',"p.vy=28*C;p.vx=(p.jumpDir or 0)*p.face*700", "p.vy=24*C;p.vx=(p.jumpDir or 0)*p.face*560")
 edit('teaching/gf_sim_lumine_training.lua',"m.dur=m.windProjectile and 8 or m.dur", "m.dur=m.windProjectile and 8 or m.dur;m.recovery=m.windProjectile and 12 or m.recovery")
 edit('teaching/gf_sim_lumine_training.lua',"local hit=clone(m);hit.push=5;hit.blockstun=16;hit.level='mid';hit.energy=4", "local hit=clone(m);hit.push=5;hit.blockstun=16;hit.level='mid';hit.energy=4;hit.launch=m.branch~='skillDown' and 18 or nil")
 edit('teaching/gf_sim_lumine_training.lua',"function T:tryCancel(p,m)\n if", '''function T:tryCancel(p,m)
 if p.key=='lumine' and p.moveId=='crouchHeavy' and p.trainingLaunchHit and p.connected and p.t<=m.startup+m.active+8 and p.inPressed&256~=0 then
  if p.energy<10 then self:emit({type='comboCancelDenied',p=p.id,cost=10});return false end
  p.energy=p.energy-10;self:setState(p,'dash');p.vx=p.face*math.floor(p.kit.body.dash*C)*22//10
  self:emit({type='dash',p=p.id,comboCancel=true});return true
 end
 if''')
 edit('battle/gf_battle_events.lua',"        if ty == 'skillFeedback' then", "        if ty=='comboCancelDenied' then\n            local p=sim.f[e.p];fx:number(p.x/C,p.y/C+210,0,'anemo',false,'追击取消需要10能量')\n        elseif ty == 'skillFeedback' then")
 import sys
 sys.path.insert(0,str(ROOT/'runtime/tools'));from import_wind_fx import build as import_fx
 effectPeak=import_fx(OUT)
 p=OUT/'source/teaching/gf_character_lumine_training.lua';code=p.read_text(encoding='utf-8');start=code.index('function P.drawWind(');end=code.rindex('return P\nend')
 code=code[:start]+(ROOT/'runtime/tools/gf_traveler_wind_view.lua').read_text(encoding='utf-8')+'\n'+code[end:];p.write_text(code,encoding='utf-8')
 edit('battle/gf_scene_fight.lua','function S:drawProj()\n    local L = self.projL', 'function S:drawProj()\n    local windUsed=false\n    local L = self.projL')
 edit('battle/gf_scene_fight.lua',"                require('gf_character_lumine_training').drawWind", "                windUsed=true\n                require('gf_character_lumine_training').drawWind")
 p=OUT/'source/battle/gf_scene_fight.lua';code=p.read_text(encoding='utf-8');start=code.index('function S:drawProj()');end=code.index('------------------------------------------------------------------ pause',start)
 chunk=code[start:end];assert chunk.count('    L:finish()')==1;chunk=chunk.replace('    L:finish()',"    if not windUsed then require('gf_character_lumine_training').clearWind(L)end\n    L:finish()")
 code=code[:start]+chunk+code[end:];code=code.replace('if self.projL then self.projL:free() end',"if self.projL then require('gf_character_lumine_training').freeWind(self.projL);self.projL:free() end");p.write_text(code,encoding='utf-8')
 edit('battle/gf_battle_events.lua',"            fx:hitSpark(x, y, e.element, e.heavy or e.kind == 'skill', a.face, e.kind)", "            if a.key=='lumine' and e.kind=='skill' and e.element=='anemo' then\n                self.views[e.by].windImpact={x=x,y=y,face=a.face,at=sim.tick}\n            else fx:hitSpark(x, y, e.element, e.heavy or e.kind == 'skill', a.face, e.kind)end")
 order=json.loads((BASE/'source/order.json').read_text(encoding='utf-8'))
 order.insert(len(order)-1,'source/teaching/gf_wind_skill_fx_data.lua');(OUT/'source/order.json').write_text(json.dumps(order,indent=2),encoding='utf-8')
 (OUT/'genshin_fighter.lua').write_text('\n'.join((OUT/p).read_text(encoding='utf-8')for p in order),encoding='utf-8')
 result={'clientSha256':sha(OUT/'genshin_fighter.lua'),'baselineSha256':sha(BASE/'genshin_fighter.lua'),'onlyChangedSourceFiles':[p for p in order if not(BASE/p).exists() or sha(BASE/p)!=sha(OUT/p)],'effectPeak':effectPeak,'bodyBudgetSeparate':True,'scope':'authored wind effect frames; confirmed launcher->E and resource dash extension; no OTG; balance/art/device acceptance pending'}
 (OUT/'build-manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':build()
