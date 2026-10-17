__loaders['gf_training_extended']=function()
local K=require('gf_kits');local G=require('gf_gfx');local UI=require('gf_ui')
local X={};X.__index=X
local function step(kind,goal,guide,extra)
 local s={kind=kind,goal=goal,guide=guide,done='做到了，旅行者！看清这次结果，我们继续下一项。'}
 for k,v in pairs(extra or {})do s[k]=v end;return s
end
local plans={
 low={step('crouchLight','蹲轻命中一次','按住下方向，再用轻击。保持低姿态，让剑碰到丘丘王。'),step('crouchHeavy','蹲重命中一次','按住下方向，再用重击。这记低位挑斩准备和收招都更长，命中会把对手挑空。')},
 air={step('airLight','跳起，用空轻命中并落地','旅行者，先起跳再轻击。空中攻击要真的命中，最后落地站稳。'),step('airHeavy','跳起，用空重命中并落地','这次起跳后用重击，向下出剑，再等到落地恢复。')},
 skill={step('skill','普通 E 命中','松开上下方向，使用向前搓出并推出风球。要在有效距离内命中哦！'),step('skillUp','上 E 命中','上方向和 E 一起按，腾空后向前下方投出风球。'),step('skillDown','下 E 命中','下方向和 E 一起按，挥剑放出贴近地面的风刃。'),step('skillCooldown','冷却时尝试 E，再等就绪命中','三个方向共用冷却。先试一次，看到冷却提示；等它就绪，再用 E 命中。')},
 burst={step('burstEmpty','能量不足时尝试大招','先看能量！现在没有充满，试着按大招，看看能量不足的提示。'),step('burstHit','用满能量大招命中','现在能量充满啦！松开方向，释放大招，确认它实际命中。'),step('burstMiss','在远处释放大招并完成收招','这次离得远一些，观察大招打空：能量照样会消耗，收招也要等完。'),step('burstBlock','让丘丘王防住一次大招','丘丘王这次会站防。用大招攻击它，看看被防住和命中的区别。')},
 assist={step('supportHit','呼叫空支援，命中并退场','这次空来帮忙！按支援键，他会入场出剑，再自行离开。你仍然控制旅行者。'),step('supportCooldown','冷却时尝试支援，再等就绪命中','先试试再次呼叫，看到冷却提示；等支援就绪，再呼叫空命中。'),step('supportMiss','远距离呼叫支援，观察打空退场','现在距离很远。呼叫空，观察这次支援打空后退场，不能凭空打中哦。')},
 throw={step('throwHit','近身投技成功造成伤害','旅行者，靠近后按投技。先伸手准备，抓住后再完成投掷。'),step('throwTech','被抓住后，在窗口内拆投','丘丘王会先准备再抓。看到被抓住的提示后，尽快按投技拆开；太早或太晚都不算。'),step('throwMiss','远距离投空，并等收招结束','拉开距离后按投技。够不到就会投空，收招期间有风险。')},
 side={step('crossRight','向右跳过丘丘王，落地自动转身','换边单独练！向前斜跳越过丘丘王，落地后，旅行者会自动面对左边的对手。'),step('crossLeft','向左跳回，落地自动转身','现在你在右边。向左斜跳越过它，落地后会重新面向右边。左右键仍是绝对方向。'),step('sideGuard','站在右侧，按新的后方向防住','这次你在对手右侧。后方向变成右边，按住右方向站防一次。没有单独的转身按钮。')},
}
local elementCases={
 anemo={{'pyro','swirl'},{'hydro','swirl'},{'electro','swirl'},{'cryo','swirl'}},
 geo={{'pyro','crystal'},{'hydro','crystal'},{'electro','crystal'},{'cryo','crystal'}},
 electro={{'hydro','electro'},{'pyro','overload'},{'cryo','superconduct'},{'dendro','quicken'},{'quickened','aggravate'},{'hydro','bloomChain',finish='electro',reaction='hyperbloom'}},
 dendro={{'hydro','bloom'},{'electro','quicken'},{'quickened','spread'},{'pyro','burning'}},
 hydro={{'pyro','vaporize'},{'cryo','frozen'},{'electro','electro'},{'dendro','bloom'}},
 pyro={{'hydro','vaporize'},{'cryo','melt'},{'electro','overload'},{'dendro','burning'},{'hydro','bloomChain',finish='pyro',reaction='burgeon'}},
 cryo={{'hydro','frozen'},{'pyro','melt'},{'electro','superconduct'}},
}
local conclusions={swirl='扩散成功！风会与已有的水、火、雷、冰附着反应。',crystal='结晶成功！产生的是晶片，走近拾取后才有护盾。',electro='感电成功！水和雷相遇，会带来后续伤害。',overload='超载成功！火与雷相遇，这里会造成额外伤害和击飞。',superconduct='超导成功！冰与雷相遇，后续物理攻击会更有效。',quicken='原激化形成了！之后再用雷或草，才是超激化或蔓激化。',aggravate='超激化成功！这是雷攻击命中原激化目标后的强化。',spread='蔓激化成功！这是草攻击命中原激化目标后的强化。',frozen='冻结成功！水与冰相遇，怪物暂时无法行动。',bloom='绽放成功！水与草生成草原核，原核会在稍后爆裂。',burning='燃烧成功！火与草相遇，会继续造成伤害。',hyperbloom='超绽放成功！先生成草原核，再由雷元素触发。',burgeon='烈绽放成功！先生成草原核，再由火元素触发。'}
function X.steps(course)
 if plans[course] then return plans[course]end
 local cases=elementCases[course];if not cases then return nil end
 local out={}
 for i,c in ipairs(cases)do
  local r=c.reaction or c[2];local aura=c[1]=='quickened' and '原激化' or K.elementName[c[1]]..'附着'
  local branch=({'skill','skillUp','skillDown'})[(i-1)%3+1]
  local key=branch=='skillUp' and '上 E' or branch=='skillDown' and '下 E' or '普通 E'
  local guide='丘丘王现在是'..aura..'。用'..K.elementName[course]..'元素的'..key..'命中，触发'..K.reactionName[r]..'。普通剑击不算哦。'
  if c[2]=='bloomChain' then guide='丘丘王先挂水。先用草元素普通 E 生成草原核，再用'..K.elementName[course]..'元素普通 E 命中原核，触发'..K.reactionName[r]..'。派蒙会帮你切换元素。';branch='skill'end
  local done=conclusions[r]
  if r=='vaporize' then done=course=='hydro' and '蒸发成功！水打火附着，触发伤害按两倍基础倍率放大。' or '蒸发成功！火打水附着，触发伤害按一点五倍基础倍率放大。'end
  if r=='melt' then done=course=='pyro' and '融化成功！火打冰附着，触发伤害按两倍基础倍率放大。' or '融化成功！冰打火附着，触发伤害按一点五倍基础倍率放大。'end
  out[#out+1]=step('reaction',K.elementName[course]..'：触发'..K.reactionName[r],guide,{aura=c[1],reaction=r,branch=branch,chain=c[2]=='bloomChain',element=course,done=done})
 end
 if course=='geo' then
  out[#out+1]=step('pickup','触发结晶，再靠近拾取晶片','怪物先挂火。用岩元素普通 E 产生晶片，再走近晶片获得护盾。直接施法不会自动给盾。')
  out[#out+1]=step('shield','用结晶护盾承受一次攻击','护盾已经装备！先松开方向，等丘丘王攻击，观察护盾吸收伤害。')
 elseif course=='cryo' then
  out[#out+1]=step('shatter','冻结怪物，再用重击触发碎冰','丘丘王先挂水。先用冰元素普通 E 冻结，再松开方向按重击，触发碎冰。')
 end
 return out
end
function X.new(lesson)return setmetatable({lesson=lesson,label='准备中'},X)end
function X:prepare(kind)
 local s=self.lesson.scene.sim;local carry=s.assistCd;local shield=s.f[1].shield
 self.kind=kind;self.age=0;self.done=false;self.seen=false;self.rejected=false;self.retry=0;self.wrong=false;self.chainReady=false;self.label='准备：按提示操作'
 s:resetObjects();s.proj={};s.freeze=0;s:setElement('anemo')
 for i,p in ipairs(s.f)do
  local held=p.inNow or 0;s:setState(p,'idle');p.x=i==1 and -9000 or 9000;p.face=i==1 and 1 or -1;p.y=0;p.vx=0;p.vy=0;p.hitstop=0;p.stun=0;p.invul=0;p.ko=false;p.airMove=nil;p.frozen=0;p.dots={};p.coat=0;p.vuln=0;p.shield=0;p.shieldT=0;p.hp=p.maxhp;p.energy=0;p.skillCd=0;p.quickened=0;p.aura=nil;p.auraT=0;p.techT=0;p.inNow=0;p.inPrev=0;p.inPressed=0;p.releaseMask=held&2032;p.lastBack=-100;p.lastFwd=-100;p.hist={};p.histN=0
 end
 local a,b=s.f[1],s.f[2];local target=self.lesson.lessons[self.lesson.index]
 if kind=='throwHit' or kind=='throwTech' then a.x=-8000;b.x=8000 end
 if kind=='burstHit' or kind=='burstBlock' or kind=='burstMiss' then a.energy=100 end
 if kind=='burstMiss' or kind=='throwMiss' or kind=='supportMiss' then a.x=-45000;b.x=45000 end
 if kind=='skillCooldown' then a.skillCd=90 end
 if kind=='supportCooldown' then s.assistCd=math.max(90,carry)end
 if kind=='crossLeft' or kind=='sideGuard' then a.x=9000;b.x=-9000;a.face=-1;b.face=1 end
 if kind=='reaction' then
  s:setElement(target.chain and 'dendro' or target.element)
  if target.aura=='quickened' then b.quickened=1200 else b.aura=target.aura;b.auraT=36000 end
 elseif kind=='pickup' then s:setElement('geo');b.aura='pyro';b.auraT=36000
 elseif kind=='shield' then a.shield=math.max(shield,120);a.shieldT=360
 elseif kind=='shatter' then s:setElement('cryo');b.aura='hydro';b.auraT=36000 end
end
function X:input()
 if self.lesson.pending>0 then return 0 end
 local s=self.lesson.scene.sim;local b=s.f[2]
 if self.kind=='burstBlock' then return b.foe.x>b.x and 4 or 8 end
 if self.kind=='sideGuard' and self.age%210==1 then return 16 end
 if self.kind=='shield' and self.age%210==50 then return 16 end
 if self.kind=='throwTech' and self.age%180==50 then return 512 end
 return 0
end
function X:tick()
 local s=self.lesson.scene.sim;local a,b=s.f[1],s.f[2];local target=self.lesson.lessons[self.lesson.index]
 self.age=self.age+1;local kind=self.kind
 local move=a.airMoveId or a.moveId
 for _,e in ipairs(s.events)do
  if (kind=='crouchLight' or kind=='crouchHeavy' or kind=='airLight' or kind=='airHeavy') and e.type=='hit' and e.by==1 and e.p==2 and (e.move==kind or a.airMove and a.airMoveId==kind) then self.seen=true end
  if (kind=='skill' or kind=='skillUp' or kind=='skillDown' or kind=='skillCooldown') and e.type=='hit' and e.by==1 and e.kind=='skill' and (kind=='skillCooldown' or e.move==kind) then self.done=kind~='skillCooldown' or self.rejected end
  if e.type=='skillFeedback' and e.p==1 and e.code=='cooldown' then self.rejected=true end
  if kind=='burstEmpty' and e.type=='skillFeedback' and e.skill=='burst' and e.code=='energy' then self.done=true end
  if kind=='burstHit' and e.type=='hit' and e.by==1 and e.kind=='burst' then self.done=true end
  if kind=='burstBlock' and e.type=='block' and e.by==1 and a.state=='burst' then self.done=true end
  if kind=='throwHit' and e.type=='hit' and e.by==1 and e.kind=='throw' then self.done=true end
  if kind=='throwTech' and e.type=='throwTech' and e.p==1 then self.done=true end
  if kind=='sideGuard' and e.type=='block' and e.p==1 and a.x>b.x and a.inNow&8~=0 then self.done=true end
  if e.type=='supportDenied' and e.code=='cooldown' then self.rejected=true end
  if e.type=='supportContact' and e.outcome=='hit' then self.seen=true end
  if kind=='reaction' and e.type=='reaction' and e.by==1 then
   if e.r==target.reaction and a.moveId~=target.branch then self.wrong=true;self.lesson:showRetry('反应发生了，但这一项目标要用指定方向的 E。等冷却好，再按提示试一次。')end
   if target.chain and e.r=='bloom' then s:setElement(target.element);a.skillCd=0;self.label='草原核已生成：再用'..K.elementName[target.element]..'元素普通 E 命中原核';self.chainReady=true end
   if e.r==target.reaction and e.r~='bloom' and a.moveId==target.branch then self.done=true end
   if e.r=='bloom' and target.reaction=='bloom' and a.moveId==target.branch then self.done=true end
  end
  if kind=='pickup' and e.type=='crystalPickup' then self.done=true end
  if kind=='shield' and e.type=='shieldHit' and e.p==1 then self.done=true end
  if kind=='shatter' and e.type=='reaction' and e.r=='shatter' then self.done=true end
 end
 if kind=='crouchLight' or kind=='crouchHeavy' then self.done=self.seen end
 if kind=='airLight' or kind=='airHeavy' then self.done=self.seen and a.y==0 and a.state=='idle'end
 if kind=='burstMiss' and a.state=='burst' then self.seen=true end
 if kind=='throwMiss' and a.moveId=='throwWhiff' then self.seen=true end
 if kind=='supportMiss' and s.assist then self.seen=true end
 if kind=='burstMiss' or kind=='throwMiss' then self.done=self.seen and a.state=='idle' end
 if kind=='supportMiss' then self.done=self.seen and not s.assist end
 if kind=='supportHit' or kind=='supportCooldown' then self.done=self.seen and not s.assist and (kind~='supportCooldown' or self.rejected)end
 if kind=='crossRight' then self.done=a.x>b.x and a.y==0 and a.state=='idle' and a.face==-1 end
 if kind=='crossLeft' then self.done=a.x<b.x and a.y==0 and a.state=='idle' and a.face==1 end
 if kind=='throwTech' then
  if a.state=='thrown' then self.label='被抓住了！现在按投技，拆投窗口12拍'
  elseif b.moveId=='throwStart' then self.label='丘丘王正在伸手准备：先别按拆投'
  elseif self.age%180==0 and not self.done then self:prepare(kind);self.lesson:showRetry('再试一次，旅行者！等被抓住后再按投技，准备阶段按不算拆投。') end
 elseif kind=='reaction' then
  if not self.chainReady then self.label='旅行者：'..K.elementName[a.element]..'  ·  目标：'..(b.aura and K.elementName[b.aura]..'附着' or (b.quickened or 0)>0 and '原激化' or '无附着')..'  ·  '..K.reactionName[target.reaction]end
  -- A wrong branch can legitimately consume aura, but cannot complete the target. Restore the setup after recovery.
  if not self.done and not target.chain and (self.wrong or not b.aura and (b.quickened or 0)==0) and a.state=='idle' and a.skillCd==0 then
   b.quickened=target.aura=='quickened' and 1200 or 0;b.aura=target.aura~='quickened' and target.aura or nil;b.auraT=36000;self.wrong=false
  end
 else
  local m=a.airMove or a.move;local t=a.airMove and a.airT or a.t
  if m and m.startup then self.label=t<m.startup and '前摇：动作正在准备' or t<m.startup+(m.active or m.dur or 6) and '出手：攻击生效' or '收招：等待动作恢复'
  else self.label=('能量 %d/100 · E %s · 支援 %s'):format(a.energy,a.skillCd>0 and ('%.1f秒'):format(a.skillCd/60) or '就绪',s.assistCd>0 and ('%.1f秒'):format(s.assistCd/60) or '就绪')end
 end
 return self.done
end
function X:hint(device,pad)
 local kind=self.kind;local branch=self.lesson.lessons[self.lesson.index].branch
 local light=device=='touch' and '点「轻」' or device=='pad' and '按 '..pad.light or '按 J'
 local heavy=device=='touch' and '点「重」' or device=='pad' and '按 '..pad.heavy or '按 K'
 local skill=device=='touch' and '点「E」' or device=='pad' and '按 '..pad.skill or '按 E'
 local throw=device=='touch' and '点「投」' or device=='pad' and '按 '..pad.throw or '按 L'
 if kind=='crouchLight' or kind=='crouchHeavy' then return (device=='touch' and '摇杆下推＋' or device=='pad' and '左摇杆下推＋' or '按住 S＋')..(kind=='crouchLight' and light or heavy)end
 if kind=='airLight' or kind=='airHeavy' then return (device=='touch' and '点「跳」→' or device=='pad' and '按 '..pad.jump..'→' or 'W/空格起跳→')..(kind=='airLight' and light or heavy)..'，命中后落地'end
 if kind=='crossRight' or kind=='crossLeft' then return (device=='touch' and '摇杆' or device=='pad' and '左摇杆' or '')..(kind=='crossRight' and (device=='pc' and 'W＋D' or '右上斜推') or (device=='pc' and 'W＋A' or '左上斜推'))..'，落地松开方向'end
 if kind=='sideGuard' then return device=='pc' and '持续按住 D：你在右侧，后方向是右' or '摇杆持续向右推：你在对手右侧'end
 if kind:find('support') then return device=='touch' and '点「援」呼叫空，观察支援冷却' or device=='pad' and '同时按 '..pad.dash..'＋'..pad.heavy..' 呼叫空' or '按 G 呼叫空，观察支援冷却'end
 if kind:find('throw') then return throw..(kind=='throwTech' and '：被抓住后12拍内按，提前按无效' or '：近身抓投，远处投空')end
 if kind:find('burst') then return device=='touch' and '点「Q」，观察能量与实际结果' or device=='pad' and '按 '..pad.burst..'，观察能量与实际结果' or '按 Q，观察能量与实际结果'end
 if kind=='pickup' then return skill..' 结晶 → 靠近地上的菱形晶片'end
 if kind=='shield' then return '松开全部方向，等待攻击命中护盾'end
 if kind=='shatter' then return skill..' 冻结 → 松开方向 → '..heavy end
 branch=branch or (kind=='skillCooldown' and 'skill' or kind)
 local dir=branch=='skillUp' and (device=='pc' and 'W＋' or '摇杆上推＋') or branch=='skillDown' and (device=='pc' and 'S＋' or '摇杆下推＋') or '松开方向，'
 return dir..skill..'；实际命中才算完成'
end
function X:drawWorld()
 local scene=self.lesson.scene;local s=scene.sim
 self.world=self.world or G.layer(scene.lay.fx);local L=self.world;L:begin()
 local b=s.f[2];local element=b.aura;local color=K.elementColor[element or 'dendro']
 if element or (b.quickened or 0)>0 then L:shape(G.RING,b.x/100,b.y/100+180,180,260,color,.5);L:label(element and K.elementName[element] or '原激化',b.x/100,b.y/100+460,260,35,24,color,'c')end
 for _,core in ipairs(s.cores)do L:shape(G.ELLIPSE,core.x/100,32,42,60,K.elementColor.dendro,1);L:label('草原核',core.x/100,85,150,30,18,UI.CREAM,'c')end
 for _,crystal in ipairs(s.crystals)do L:shape(G.RECT,crystal.x/100,45,36,36,K.elementColor[crystal.element],1,45)end
 if s.f[1].shield>0 then L:shape(G.RING,s.f[1].x/100,150,190,300,K.elementColor.geo,.7)end
 L:finish()
 if self.lesson.course=='assist' or s.assist or self.support then
  local D=require('gf_aether_support_data');local P=require('gf_aether_support')
  self.support=self.support or {G.bitmap(scene.lay.body),G.bitmap(scene.lay.body)}
  local a=s.assist
  if a then
   local index=a.t<20 and 1 or a.t<26 and 2 or a.t<45 and 3 or 4
   local key='assist_'..(index-1);local image=P.image(key);local slot=self.support[index%2+1]
   if slot.key~=key and (not slot.job or slot.job.key~=key) then slot.node:on(false);slot:start(image,key)end
   if slot.job then slot:step(240)end
   if not slot.job then
    local other=self.support[index%2==0 and 2 or 1];other.node:on(false)
    slot.node:pos(a.x/100,0):scale(a.face,1):on(true)
    if index<4 then
     local nextKey='assist_'..index;local nextImage=P.image(nextKey)
     if other.key~=nextKey and (not other.job or other.job.key~=nextKey)then other:start(nextImage,nextKey)end
     if other.job then other:step(160)end
    end
   end
  else for _,bmp in ipairs(self.support)do bmp.node:on(false)end end
 end
end
function X:free()if self.world then self.world:free()end;if self.support then for _,b in ipairs(self.support)do b:free()end end end
return X
end
