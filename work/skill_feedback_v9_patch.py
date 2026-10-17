from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parents[1]
O=R/'outputs/skill-feedback-20261014';O.mkdir(exist_ok=True)
def read(rel):
 p=R/rel; h=O/'history'/rel;h.parent.mkdir(parents=True,exist_ok=True)
 if not h.exists():shutil.copy2(p,h)
 return p,p.read_text(encoding='utf8')
def write(p,s):p.write_text(s,encoding='utf8')
# Delivered adapters keep their own independent forward distances.
for key,reach in [('furina',410),('ayaka',420),('clorinde',410),('arlecchino',410)]:
 p,s=read(f'runtime/source/battle/gf_sim_{key}.lua')
 s=s.replace('dx>=-40*C and dx<=380*C and d.y<420*C',f"dx>=-40*C and self:burstTouches(p,d,{reach}) and d.y<420*C")
 s=s.replace("heavy=true})","heavy=true,kind='burst'})",1)
 write(p,s)
p,s=read('runtime/source/battle/gf_sim.lua')
s=s.replace("require('gf_sim_team')(S,newFighter,C)","require('gf_sim_team')(S,newFighter,C)\nrequire('gf_sim_feedback')(S,ctx)")
write(p,s)
p,s=read('runtime/source/battle/gf_sim_actions.lua')
# Stage-wide Nahida needs edge intersection, not more stage coverage.
s=s.replace('math.abs(d.x-p.x)<=bu.range*C','self:burstTouches(p,d,bu.range)',1)
s=s.replace('math.abs(d.x-p.x)<=bu.range*C and d.y<420*C',"(d.x-p.x)*p.face>=-bu.range*C and self:burstTouches(p,d,950) and d.y<420*C",1)
write(p,s)
p,s=read('runtime/source/battle/gf_sim_combat.lua')
s=s.replace("heavy = (m.damage or 0) >= 60})","heavy = (m.damage or 0) >= 60, kind = kind})")
write(p,s)
p,s=read('runtime/source/network/gf_online.lua');write(p,s.replace('O.VERSION = 6','O.VERSION = 7'))
p,s=read('runtime/source/order.json');a=json.loads(s);a.insert(a.index('source/battle/gf_sim_team.lua')+1,'source/battle/gf_sim_feedback.lua');write(p,json.dumps(a,ensure_ascii=False,indent=2)+'\n')
p,s=read('runtime/source/characters/gf_character_clorinde_view.lua')
s=s.replace("  if not g or (id=='burst' and not f.cinematicConfirmed) then return out end", "  local impact=v.confirmedImpact\n  if impact and v.app.t<impact.untilTime then\n   out[3]={id=D.effectIds.impact,x=impact.x,y=impact.y,face=impact.face,alpha=math.min(1,(impact.untilTime-v.app.t)/.12),scale=1}\n  end\n  if not g or (id=='burst' and not f.cinematicConfirmed) then return out end")
s=s.replace("    if age>=3 then local image=D.effectIds.impact;out[3]={id=image,x=f.foe.x/100,y=f.foe.y/100+190,face=face,alpha=(8-age)/5,scale=1} end\n",'')
write(p,s)
p,s=read('runtime/source/battle/gf_battle_events.lua')
s=s.replace("        if ty == 'hit' then", "        if ty == 'skillFeedback' then\n            self.hud:skillFeedback(e)\n        elseif ty == 'hit' then",1)
s=s.replace("            local x, y = e.x / C, e.y / C", "            local x, y = e.x / C, e.y / C\n            if a.key=='clorinde' and (e.kind=='skill' or e.kind=='burst' or e.kind=='light' or e.kind=='heavy') then\n                self.views[e.by].confirmedImpact={x=x,y=y,face=a.face,untilTime=app.t+.12}\n            end",1)
write(p,s)
p,s=read('runtime/source/render/gf_hud.lua')
s=s.replace('local PR = 56', '''-- Two fixed HUD messages; confirmed events only, no repeated allocations per press.
local FEEDBACK={energy='能量不足',cooldown='战技冷却中',state='当前动作不能释放',miss='未命中，已收招',block='被防住'}
function H:skillFeedback(e)
    self.skillMessages=self.skillMessages or {}
    local old=self.skillMessages[e.p];local now=self.app.t
    if old and old.code==e.code and now<old.untilTime then return end
    self.skillMessages[e.p]={code=e.code,text=FEEDBACK[e.code] or '',untilTime=now+.85,round=self.sim.round}
end

local PR = 56''')
needle='        local ek = U.clamp(f.energy / 100, 0, 1)'
s=s.replace(needle,"        local msg=self.skillMessages and self.skillMessages[i]\n        local visible=msg and msg.round==sim.round and app.t<msg.untilTime and sim.phase=='fight'\n        L:label(visible and msg.text or '',gcx,gy-30,gw+100,28,20,GOLD,'c',SHADOW,visible and 1 or 0)\n"+needle)
write(p,s)
print('patched source; rules protocol 7')
