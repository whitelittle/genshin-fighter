__loaders['gf_team_server']=function()
-- Executable reference for the new server node graph; never runs on the native client.
local S={};S.__index=S
function S.new() return setmetatable({epoch=1,players=0,teams={{},{ }},ready={false,false},revision={-1,-1},locked=false},S) end
function S:handle(name,p,players)
 local out={};local function send(slot,signal,values) out[#out+1]={slot=slot,signal=signal,params=values} end
 local function both(signal,values) for q=1,math.min(2,self.players) do send(q,signal,values) end end
 local function progress()
  for q=1,2 do both('GF3Progress',{self.epoch,q,#self.teams[q],self.ready[q] and 1 or 0,self.revision[q]}) end
 end
 local function reveal()
  local a,b=self.teams[1],self.teams[2]
  both('GF3Reveal',{self.epoch,self.revision[1],self.revision[2],a[1],a[2],a[3],b[1],b[2],b[3]})
 end
 local function seat() for q=1,math.min(2,self.players) do send(q,'GF3Seat',{q,self.epoch}) end end
 if name=='GF3Hello' then
  self.players=math.min(2,players or self.players);seat();progress()
  if self.locked then reveal() end
  return out
 end
 local lengths={GF3Team=7,GF3Reset=2}
 if #p~=(lengths[name] or -1) and not(name=='GF3Reset' and #p==3) then return out end
 for _,v in ipairs(p) do if type(v)~='number' or v%1~=0 then return out end end
 local q=p[1]
 if (q~=1 and q~=2) or q>self.players or p[2]~=self.epoch then return out end
 if name=='GF3Reset' then
  local nextEpoch=p[3] or self.epoch+1;if nextEpoch<=self.epoch then return out end
  self.epoch=nextEpoch;self.teams={{},{}};self.ready={false,false};self.revision={-1,-1};self.locked=false
  seat();progress();return out
 end
 local rev=p[3];local ready=p[7]
 if rev<0 or rev<self.revision[q] or (ready~=0 and ready~=1) then return out end
 local team,seen={},{};local gap=false
 for i=4,6 do local v=p[i]
  if v<0 or v>6 then return out end
  if v==0 then gap=true elseif gap or seen[v] then return out else team[#team+1]=v;seen[v]=true end
 end
 if ready==1 and #team~=3 then return out end
 if self.locked or rev==self.revision[q] then
  if rev~=self.revision[q] or ready~=(self.ready[q] and 1 or 0) or #team~=#self.teams[q] then return out end
  for i,v in ipairs(team) do if self.teams[q][i]~=v then return out end end
  progress();if self.locked then reveal() end;return out
 end
 self.teams[q]=team;self.ready[q]=ready==1;self.revision[q]=rev
 progress()
 if self.ready[1] and self.ready[2] then self.locked=true;reveal() end
 return out
end
return S
end
