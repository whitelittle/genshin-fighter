__loaders['gf_training_coach']=function()
-- Local lesson controller. All timing follows simulation ticks, never UI time.
local C={};C.__index=C
function C.new(lesson)return setmetatable({lesson=lesson},C)end
function C:prepare(kind)
 self.kind=kind;self.age=0;self.retry=0;self.missed=false;self.punishWindow=false;self.success=false
 local sim=self.lesson.scene.sim
 for i,p in ipairs(sim.f)do
  sim:setState(p,'idle');p.y=0;p.vx=0;p.vy=0;p.hitstop=0;p.stun=0;p.invul=0;p.ko=false;p.airMove=nil
  p.hp=p.maxhp;p.inNow=0;p.inPrev=0;p.inPressed=0;p.lastBack=-100;p.lastFwd=-100
  p.x=(i==1 and -1 or 1)*((kind=='evade' or kind=='punish') and 14000 or 9000)
  p.face=i==1 and 1 or -1
 end
 self.startX=sim.f[1].x
 self.label='准备：看清提示后再行动'
end
function C:input()
 local lesson=self.lesson;local sim=lesson.scene.sim;local p=sim.f[2]
 self.punishWindow=p.state=='attack' and p.move and p.t>=p.move.startup+p.move.active
 if lesson.pending>0 or not lesson.lessons[lesson.index] or self.retry>0 then return 0 end
 -- One input pulse starts the real move; its native startup/active/recovery is authoritative.
 if self.age==1 and sim.phase=='fight' then return self.kind=='crouchGuard' and (2|32) or 16 end
 return 0
end
function C:tick()
 local lesson=self.lesson;local sim=lesson.scene.sim;local a,b=sim.f[1],sim.f[2]
 self.age=self.age+1
 if self.retry>0 then
  self.retry=self.retry-1
  if self.retry==0 then self:prepare(self.kind) end
  return false
 end
 if b.state=='attack' and b.move then
  local m=b.move
  if b.t<m.startup then self.label=(self.kind=='crouchGuard' and '压低蓄力：后下方蹲防' or '举拳蓄力：后方向站防')
  elseif b.t<m.startup+m.active then self.label='攻击生效：看准距离与防御高度'
  else
   self.label='丘丘王正在收招：现在可以反击'
   if not b.connected and a.y==0 and self.startX-a.x>=3000 then self.missed=true end
  end
 end
 for _,e in ipairs(sim.events)do
  if e.type=='block' and e.p==1 then
   if self.kind=='standGuard' and a.state=='block' then self.success=true end
   if self.kind=='crouchGuard' and a.state=='cblock' then self.success=true end
  elseif e.type=='hit' and e.p==1 and e.by==2 then
   lesson.line='没关系，旅行者！看清上段或下段，再按住对应的后方向。我们再来一次。'
   self.retry=100;self.label='受击了，稍后复位重试'
  elseif e.type=='hit' and e.p==2 and e.by==1 and e.kind=='light' and self.kind=='punish' and self.missed and self.punishWindow then
   self.success=true
  end
 end
 if self.kind=='evade' and self.missed then self.success=true end
 if self.age>220 and not self.success then
  lesson.line=self.kind=='standGuard' and '再试一次吧！保持站立，按住后方向，让这一击落在站防上。'
   or self.kind=='crouchGuard' and '再试一次吧！后方向加下方向要一起按住，才能防住下段。'
   or '再试一次吧！先退开躲过这一击，看到收招提示后再靠近轻击。'
  self.retry=60;self.label='本次未完成，稍后复位重试'
 end
 return self.success
end
return C
end
