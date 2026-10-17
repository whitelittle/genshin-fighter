__loaders['gf_training_juggle']=function()
local J={};J.__index=J
J.steps={
 {kind='launch',goal='蹲重挑空，观察对手落地',guide='先靠近，按住下方向再重击。这是有明显准备和收招的挑空技，打中后对手会离地；先观察，不急着追。',done='看清挑空了！接下来练命中后的跳跃取消。'},
 {kind='chase',goal='蹲重命中后，向前追跳并落地',guide='蹲重打中后，马上按跳跃加前方向，取消收招并自己追上去。只有命中后的短窗口能接；打空或被防都不能。',done='追上去了！方向由你控制，没有自动追踪。下一步加一记空轻。'},
 {kind='airChase',goal='挑空 → 向前追跳 → 空轻命中',guide='蹲重打中，跳跃加前方向追上，然后按轻击。要在对手落地前真的打中，空挥不算。',done='空轻追击成功！最后把地面两段和空重收尾接起来。'},
 {kind='route',goal='地面轻一、轻二 → 挑空追跳 → 空轻、空重',guide='从轻击第一段开始，每次命中再按下一招：轻、轻、下加重；挑空命中后向前追跳，再轻、重。最后一击把对手打落，不能中途断连。',done='五击连段完成！这是命中确认、挑空、追跳和空中收尾的一条完整路线。'},
}
function J.new(lesson)return setmetatable({lesson=lesson,label='准备：先看清目标'},J)end
function J:prepare(kind)
 self.kind=kind;self.stage=0;self.launch=false;self.jump=false;self.chaseHit=false;self.failed=false;self.attempt=false;self.rest=0;self.done=false
 local s=self.lesson.scene.sim;s:resetObjects();s.proj={};s.freeze=0;s:setElement('anemo')
 for i,p in ipairs(s.f)do
  local held=p.inNow or 0;s:setState(p,'idle');p.x=i==1 and -9000 or 9000;p.face=i==1 and 1 or -1
  p.y=0;p.vx=0;p.vy=0;p.hitstop=0;p.stun=0;p.invul=0;p.ko=false;p.airMove=nil;p.airMoveId=nil;p.trainingChase=nil;p.trainingJumpAttack=nil;p.trainingLaunchHit=nil
  p.hp=p.maxhp;p.combo=0;p.juggle=0;p.comboDmg=0;p.inNow=0;p.inPrev=0;p.inPressed=0;p.releaseMask=held&2033;p.lastFwd=-100;p.lastBack=-100;p.hist={};p.histN=0
 end
 self.label='准备：命中后再接下一步；打空要等待收招'
end
function J:input()return 0 end
function J:tick()
 local s=self.lesson.scene.sim;local a,b=s.f[1],s.f[2];local kind=self.kind
 local route={'light1','light2','crouchHeavy','airLight','airHeavy'}
 for _,e in ipairs(s.events)do
  if e.type=='swing' and e.p==1 then self.attempt=true end
  if e.type=='jumpCancel' and e.p==1 and self.launch then self.jump=true end
  if e.type=='block' and e.by==1 then self.failed=true end
  if e.type=='hit' and e.by==1 and e.p==2 then
   if e.move=='crouchHeavy' then self.launch=true end
   if e.move=='airLight' and self.launch and self.jump and e.combo>=2 then self.chaseHit=true end
   if kind=='route' then
    if e.move=='light1' and e.combo==1 then self.stage=1;self.failed=false
    elseif not self.failed and e.move==route[self.stage+1] and e.combo==self.stage+1 then self.stage=self.stage+1
    else self.failed=true end
   end
  end
 end
 local settled=a.y==0 and a.state=='idle' and b.y==0 and (b.state=='down' or b.state=='getup' or b.state=='idle')
 local success=kind=='launch' and self.launch or kind=='chase' and self.launch and self.jump or kind=='airChase' and self.chaseHit or kind=='route' and self.stage==5 and not self.failed
 if success and settled then self.done=true;return true end
 if self.attempt and settled then
  self.rest=self.rest+1
  if self.rest>=30 then
   self:prepare(kind);self.lesson:showRetry('再来一次：先确认命中；挑空后按跳跃加前方向，空轻命中再空重。打空或断连不能继续算。')
  end
 else self.rest=0 end
 self.label=kind=='route' and ('本次路线 '..self.stage..'/5 · 每次命中后接下一招') or self.jump and '已追跳：自己控制方向，空轻追击' or self.launch and '已挑空：命中后短窗口内可以向前追跳' or '蹲重打中才可立即追跳；打空与被防要收招'
 return false
end
function J:hint(device,p)
 local face=self.lesson.scene.sim.f[1].face;local forward=face==1 and 'D' or 'A'
 if device=='touch' then return self.kind=='route' and '轻 → 轻 → 摇杆下＋重 → 前上追跳 → 轻 → 重' or '摇杆下＋重 → 命中后前上推追跳 → 轻 → 重' end
 if device=='pad' then return '下＋'..p.heavy..' → 命中后前方向＋'..p.jump..' → '..p.light..' → '..p.heavy end
 return self.kind=='route' and ('J → J → S＋K → 命中后 '..forward..'＋空格 → J → K') or ('S＋K 挑空 → 命中后 '..forward..'＋空格追跳 → J 空轻 → K 空重')
end
function J:drawWorld()end
function J:free()end
return J
end
