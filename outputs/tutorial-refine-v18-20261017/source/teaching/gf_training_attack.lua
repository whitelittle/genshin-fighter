__loaders['gf_training_attack']=function()
local A={};A.__index=A
A.steps={
 {kind='approach',goal='靠近丘丘王，进入攻击距离',guide='旅行者，先靠近丘丘王，在能碰到它的距离停下来。',done='这个距离可以出剑了。先练一次轻击命中。'},
 {kind='hit',goal='轻击命中丘丘王一次',guide='停下后用轻击攻击它。真正命中才算，远处挥空不会完成。',done='打中了！接下来把三段普攻连起来，看看连续命中的节奏。'},
 {kind='combo',goal='同一连段中命中轻击第一、二、三段',guide='每次命中后再按一下轻击，把三段连起来。长按不会自动连段；间隔太久，就从第一段重来。',done='三段都连上了！最后一击收好剑，我们再试重击。'},
 {kind='heavy',goal='松开方向，用重击命中一次',guide='现在松开方向，再按重击。看看更明显的准备和收势，确认刀刃真正碰到丘丘王。',done='重击命中了！它出手慢一些，打空后也要等动作结束。'},
 {kind='whiff',goal='在远处打空重击，并等待收招完成',guide='这次已经拉开距离。在原地出一次重击，然后等旅行者收好剑。打空不能靠命中取消来提前结束。',done='看清楚啦！打空时也有收招。普通攻击这一课完成了，旅行者！'},
}
function A.new(lesson)return setmetatable({lesson=lesson},A)end
function A:prepare(kind)
 self.kind=kind;self.progress=0;self.baseCombo=0;self.whiffSaw=false;self.whiffHitId=nil
 local sim=self.lesson.scene.sim
 for _,p in ipairs(sim.f)do p.releaseMask=(p.inNow or 0)&1008 end
 if kind~='combo' and kind~='heavy' and kind~='whiff' then return end
 for i,p in ipairs(sim.f)do
  sim:setState(p,'idle');p.x=(i==1 and -1 or 1)*(kind=='whiff' and 32500 or 9000)
  p.y=0;p.vx=0;p.vy=0;p.hitstop=0;p.stun=0;p.invul=0;p.ko=false;p.airMove=nil
  p.hp=p.maxhp;p.face=i==1 and 1 or -1;p.combo=0;p.comboDmg=0;p.juggle=0
  p.inNow=0;p.inPrev=0;p.inPressed=0;p.lastFwd=-100;p.lastBack=-100
 end
end
function A:tick()
 local sim=self.lesson.scene.sim;local p,d=sim.f[1],sim.f[2];local kind=self.kind
 if kind=='approach' then return math.abs(d.x-p.x)<=20000 end
 for _,e in ipairs(sim.events)do
  if kind=='whiff' and e.type=='swing' and e.p==1 and e.move=='heavy' then self.whiffSaw=true;self.whiffHitId=p.hitId end
  if (e.type=='hit' or e.type=='block') and e.by==1 then
   if kind=='whiff' then
    self.whiffSaw=false;self.lesson:showRetry('这次碰到它啦！先退远一些，再打一记重击，等收招结束。')
   elseif e.type=='hit' then
    if kind=='hit' and e.move=='light1' and e.kind=='light' then return true end
    if kind=='heavy' and e.move=='heavy' and e.kind=='heavy' then return true end
    if kind=='combo' then
     if e.move=='light1' and e.kind=='light' then self.progress=1;self.baseCombo=e.combo
     elseif self.progress==1 and e.move=='light2' and e.combo==self.baseCombo+1 then self.progress=2
     elseif self.progress==2 and e.move=='light3' and e.combo==self.baseCombo+2 then self.progress=3;return true
     else self.progress=0 end
    end
   elseif kind=='combo' then self.progress=0 end
  end
 end
 if kind=='combo' and self.progress>0 and d.state~='hit' and d.state~='airhit' then
  self.progress=0;self.lesson:showRetry('间隔有点久啦！从第一段重新开始，命中后再按下一次轻击。')
 end
 if kind=='whiff' then return self.whiffSaw and p.hitId==self.whiffHitId and p.state=='idle' end
 return false
end
function A:status()
 local p=self.lesson.scene.sim.f[1];local names={light1='轻击第一段',light2='轻击第二段',light3='轻击第三段',heavy='重击'}
 if p.state=='attack' and p.move then
  local m=p.move;local phase=p.t<m.startup and '准备' or p.t<m.startup+m.active and '出手' or '收招'
  return (names[p.moveId] or '攻击')..' · '..phase
 end
 if self.kind=='combo' then return '本次连续命中 '..self.progress..'/3 · 命中后再按下一次轻击' end
 if self.kind=='whiff' then return '保持距离，出一次重击，再等收招结束' end
 return '先调整距离，停下后出招'
end
return A
end
