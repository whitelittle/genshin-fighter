__loaders['gf_team_lobby']=function()
-- Three-person preparation on the established GFV2 24-integer connection.
-- The server remains a transparent relay; combat input packets are unchanged.
local O=require('gf_online');local F=require('gf_net').F
local MAGIC=-7303
local P={}
local function roles(word,count)
 local out={};local seen={}
 for i=1,count do
  local id=(word>>((i-1)*5))&31
  if id<1 or id>#require('gf_roster') or seen[id] then return nil end
  seen[id]=true;out[i]=id
 end
 if word>>(count*5)~=0 then return nil end
 return out
end
local function pack(team)
 local word=0;for i,id in ipairs(team)do word=word|(id<<((i-1)*5)) end;return word
end
function P.new(o)
 local t={active=false,epoch=0,team={},ready=false,revision=0,remoteCount=0,remoteReady=false,remoteRevision=-1,matched=true}
 function t.start()
  o.teamDraftCounter=(o.teamDraftCounter or 0)+1
  t.generation=o.teamDraftCounter;t.active=true;t.team={};t.ready=false;t.revision=0;t.reveal=nil;t.remoteGeneration=nil;t.epoch=0;t.connected=false
  t.remoteCount=0;t.remoteReady=false;t.remoteRevision=-1;t.ackGeneration=0;t.ackRevision=-1
  o.teamDraft=t;o.me.teamMode=true;o.me.selecting=true;o.me.ready=false
 end
 function t.stop()t.active=false;o.me.ready=false end
 function t.reset()t.start() end
 function t.publish(team,ready)
  if t.ready and not ready then t.start();return true end
  local word=pack(team);if #team>4 or not roles(word,#team) or (ready and #team~=4) then return false end
  t.team={};for i,id in ipairs(team)do t.team[i]=id end
  t.ready=not not ready;t.revision=t.revision+1;t.reveal=nil;t.ackGeneration=0;t.ackRevision=-1
  o.me.ready=t.ready;o.me.char=t.team[1] or 1
  return true
 end
 function t.encode(packet)
  packet[F.frameEnd]=MAGIC;packet[F.adv]=#t.team|(t.ready and 8 or 0)
  packet[F.hashFrame]=t.generation;packet[F.hash]=t.ackGeneration
  packet[F.drop]=t.ackRevision;packet[F.inputs]=t.revision
  packet[F.seed]=t.ready and t.remoteReady and pack(t.team) or 0
 end
 function t.pump()
  if not t.active then return end
  t.slot=o.slot;local opp=O.opponent(o);local peer=opp and o.peers[opp];local p=peer and peer.pkt
  if not peer then t.connected=false;t.reveal=nil;t.remoteReady=false;t.error='等待对方重新连接';return end
  if peer.match~=0 and t.reveal then return end
  if not p or p[F.frameEnd]~=MAGIC or peer.match~=0 then t.connected=false;t.error='等待对方进入车轮战';return end
  local flags,generation,revision=p[F.adv],p[F.hashFrame],p[F.inputs]
  if flags<0 or flags>12 or generation<1 or revision<0 then return end
  local count,ready=flags&7,flags&8~=0
  if count>4 or (ready and count~=4) then return end
  if t.remoteGeneration and generation<t.remoteGeneration then return end
  if t.remoteGeneration==generation and revision<t.remoteRevision then return end
  if t.remoteGeneration and generation~=t.remoteGeneration then
   t.team={};t.ready=false;t.revision=t.revision+1;t.reveal=nil;o.me.ready=false
   t.ackGeneration=0;t.ackRevision=-1
  end
  t.remoteGeneration=generation;t.remoteRevision=revision;t.remoteCount=count;t.remoteReady=ready;t.connected=true;t.error=nil
  t.epoch=t.slot==1 and (t.generation..':'..generation) or (generation..':'..t.generation)
  if not t.ready or not ready then t.reveal=nil;t.ackGeneration=0;t.ackRevision=-1;return end
  local remote=roles(p[F.seed],4);if not remote then return end
  t.ackGeneration=generation;t.ackRevision=revision
  if p[F.hash]==t.generation and p[F.drop]==t.revision then
   t.reveal={{},{}};for i,id in ipairs(t.team)do t.reveal[t.slot][i]=id end;for i,id in ipairs(remote)do t.reveal[opp][i]=id end
  end
 end
 return t
end
return P
end
