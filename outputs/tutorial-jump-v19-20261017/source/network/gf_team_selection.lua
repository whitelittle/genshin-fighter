__loaders['gf_team_selection']=function()
-- Separate GF3 preparation protocol. No GFV2 packets, variables or handlers are reused.
local P={}
local Signals=require('gf_signal_names')
function P.new(game,script,now)
 local t={active=false,slot=nil,epoch=0,revision=0,team={},ready=false,remoteCount=0,remoteReady=false,remoteRevision=-1,last=-99}
 local function emit(name,values)
  local ok,err=pcall(function() local s=game.ServerSignal(Signals.resolve(name));for _,v in ipairs(values or {}) do s:AddInt(v) end;s:SendSignal() end)
  t.error=not ok and tostring(err) or nil
 end
 local function valid(p,n)
  if not p or #p~=n then return false end
  for i=1,n do if type(p[i])~='number' or p[i]%1~=0 then return false end end
  return true
 end
 script:RegisterServerSignalHandler(Signals.resolve('GF3Seat'),function(_,p)
  if not t.active or not valid(p,2) or (p[1]~=1 and p[1]~=2) or p[2]<t.epoch then return end
  if p[2]>t.epoch and t.hasSeat then
   t.team={};t.ready=false;t.revision=0;t.remoteRevision=-1;t.remoteCount=0;t.remoteReady=false;t.reveal=nil
  end
  t.slot=p[1];t.epoch=p[2];t.hasSeat=true;t.seatAt=now()
 end)
 script:RegisterServerSignalHandler(Signals.resolve('GF3Progress'),function(_,p)
  if not t.active or not t.slot or not valid(p,5) or p[1]~=t.epoch or p[2]==t.slot or (p[2]~=1 and p[2]~=2) then return end
  if p[3]<0 or p[3]>3 or (p[4]~=0 and p[4]~=1) or p[5]<t.remoteRevision then return end
  t.remoteRevision=p[5];t.remoteCount=p[3];t.remoteReady=p[4]==1
 end)
 script:RegisterServerSignalHandler(Signals.resolve('GF3Reveal'),function(_,p)
  if not t.active or not t.slot or not valid(p,9) or p[1]~=t.epoch or not t.ready then return end
  local teams={{p[4],p[5],p[6]},{p[7],p[8],p[9]}}
  for q=1,2 do local seen={};for _,v in ipairs(teams[q]) do if v<1 or v>6 or seen[v] then return end;seen[v]=true end end
  if p[t.slot+1]~=t.revision then return end
  for n=1,3 do if teams[t.slot][n]~=t.team[n] then return end end
  t.reveal=teams
 end)
 function t.start()
  t.active=true;t.slot=nil;t.hasSeat=false;t.last=-99;t.reveal=nil;t.team={};t.ready=false;t.revision=0
  t.remoteCount=0;t.remoteReady=false;t.remoteRevision=-1;t.startedAt=now();t.seatAt=nil
 end
 function t.publish(team,ready)
  if t.slot and t.ready and not ready then
   -- Cancel may race with the server's reveal; a new epoch prevents split rosters.
   t.ready=false;t.reveal=nil;emit('GF3Reset',{t.slot,t.epoch,t.epoch+1});return true
  end
  t.team={};for n,v in ipairs(team) do t.team[n]=v end
  t.ready=ready;t.revision=t.revision+1;t.last=-99;t.reveal=nil;return true
 end
 function t.pump()
  if not t.active or now()-t.last<.5 then return end
  t.last=now();emit('GF3Hello')
  if t.slot then emit('GF3Team',{t.slot,t.epoch,t.revision,t.team[1] or 0,t.team[2] or 0,t.team[3] or 0,t.ready and 1 or 0}) end
 end
 function t.reset() if t.slot then emit('GF3Reset',{t.slot,t.epoch,t.epoch+1}) end end
 function t.stop() t.active=false end
 return t
end
return P
end
