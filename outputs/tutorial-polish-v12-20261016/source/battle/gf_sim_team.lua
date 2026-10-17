__loaders['gf_sim_team']=function()
-- Three stocks per side. Rendering readiness never changes simulation timing.
return function(S,newFighter,C)
 local oldNew,oldFlow=S.new,S.flow
 function S.new(opts)
  if not opts.teams then return oldNew(opts) end
  local copy={};for k,v in pairs(opts)do copy[k]=v end
  for side=1,2 do assert(#opts.teams[side]==3,'team requires three fighters');local seen={}
   for _,char in ipairs(opts.teams[side])do assert(char.key and not seen[char.key],'invalid or repeated team fighter');seen[char.key]=true end
  end
  copy.chars={opts.teams[1][1],opts.teams[2][1]};copy.rounds=1;copy.training=false
  local self=oldNew(copy);self.teams=opts.teams;self.teamIndex={1,1};self.teamBout=1
  return self
 end
 function S:flow()
  if not self.teams or self.phase~='ko' or self.phaseT<90 then return oldFlow(self) end
  local winner=self.roundWinner;local advance={winner~=1 or self.f[1].hp<=0,winner~=2 or self.f[2].hp<=0}
  local exhausted={false,false}
  for side=1,2 do if advance[side] then
   self.teamIndex[side]=self.teamIndex[side]+1;exhausted[side]=self.teamIndex[side]>3
  end end
  if exhausted[1] or exhausted[2] then
   self.phase='over';self.phaseT=0
   if exhausted[1] and exhausted[2] then self.matchWinner=nil else self.matchWinner=exhausted[1] and 2 or 1 end
   self:emit({type='matchEnd',winner=self.matchWinner,team=true});return
  end
  local hp,energy={},{}
  for side=1,2 do
   hp[side],energy[side]=self.f[side].hp,self.f[side].energy
   if advance[side] then
    self.f[side]=newFighter(side,self.teams[side][self.teamIndex[side]],(side==1 and -260 or 260)*C,side==1 and 1 or -1)
    hp[side],energy[side]=self.f[side].maxhp,0
   end
  end
  self.f[1].foe,self.f[2].foe=self.f[2],self.f[1]
  self.teamBout=self.teamBout+1;self.round=self.teamBout
  self:startRound(false)
  for side=1,2 do self.f[side].hp=hp[side];self.f[side].energy=energy[side] end
  self:emit({type='teamSwap',index1=self.teamIndex[1],index2=self.teamIndex[2],bout=self.teamBout})
 end
end
end
