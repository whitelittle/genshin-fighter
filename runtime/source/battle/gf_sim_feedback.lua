__loaders['gf_sim_feedback']=function()
-- Feedback uses existing input edges and outcomes, with no extra mutable simulation fields.
return function(S,ctx)
 local C,B=ctx.C,ctx.B
 function S:burstTouches(p,d,forward)
  local a,b=self:hurtbox(d)
  if not a or d.ko then return false end
  -- Preserve centre-based rear boundary in callers; only the front checks body edges.
  local near=p.face==1 and a-p.x or p.x-b
  return near<=forward*C
 end
 local oldBurst=S.burstUpdate
 function S:burstUpdate(p)
  local confirm=p.key=='furina' and 12 or p.key=='kamisatoayaka' and 52
      or (p.key=='clorinde' or p.key=='arlecchino') and 6
      or (p.key=='nahida' or p.key=='raidenshogun') and 2
  local first=confirm and p.t==confirm and not p.cinematicConfirmed
  local n=#self.events
  oldBurst(self,p)
  if first and not p.cinematicConfirmed then
   local blocked=false
   for i=n+1,#self.events do local e=self.events[i];if e.type=='block' and e.by==p.id then blocked=true end end
   self:emit({type='skillFeedback',p=p.id,skill='burst',code=blocked and 'block' or 'miss'})
  end
 end
 local oldStep=S.step
 function S:step(a,b)
  local bursts={self.f[1].stats.bursts,self.f[2].stats.bursts}
  oldStep(self,a,b)
  if self.phase~='fight' then return end
  for i,p in ipairs(self.f) do
   local pr=p.inPressed or 0
   if pr&B.BU~=0 and p.stats.bursts==bursts[i] then
    self:emit({type='skillFeedback',p=i,skill='burst',code=p.energy<100 and 'energy' or 'state'})
   elseif pr&B.SK~=0 and pr&B.BU==0 then
    local started=false
    for _,e in ipairs(self.events) do if e.type=='skill' and e.p==i then started=true end end
    if not started then self:emit({type='skillFeedback',p=i,skill='skill',code=p.skillCd>0 and 'cooldown' or 'state'}) end
   end
  end
 end
end
end
