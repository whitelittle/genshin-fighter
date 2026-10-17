-- Frame journals use a separate monotonic network clock; round resets never reset it.
local function NewRollbackSession(callbacks,slot)
 local r={frame=0,confirmed=0,peerAck=0,localFrames={},remoteFrames={},used={},history={},pending={},dirty=nil,rollbacks=0,replayed=0,stalled=false,error=nil}
 local allowed={left=true,right=true,down=true,block=true,jump=true,light=true,heavy=true,clickLight=true,clickHeavy=true,stick=true,role=true,stage=true,restart=true}
 local function fail(message)r.error=message;return false end
 local function encode(events)
  local parts={};for _,e in ipairs(events)do parts[#parts+1]=e[1]..':'..e[2]end
  return #parts==0 and '-' or table.concat(parts,',')
 end
 local function decode(s)
  if s=='-' then return {}end
  local events={}
  for item in string.gmatch(s,'[^,]+')do
   local event,value=string.match(item,'^([%a]+):(%-?%d+)$');value=tonumber(value)
   if not allowed[event] or not value or value<0 or value>9 or #events>=32 then return nil end
   events[#events+1]={event,value}
  end
  if #events==0 or encode(events)~=s then return nil end
  return events
 end
 function r:queue(event,value)
  if self.error then return end
  if not allowed[event] or #self.pending>=32 then fail('INPUT_OVERFLOW');return end
  self.pending[#self.pending+1]={event,value==nil and 1 or value}
 end
 local function simulate(n)
  r.history[n]=callbacks.capture()
  local remote=r.remoteFrames[n] or '-';r.used[n]=remote
  local bySlot={};bySlot[slot]=decode(r.localFrames[n]);bySlot[3-slot]=decode(remote)
  -- Always apply player 1 then player 2, including simultaneous reset/role events.
  for player=1,2 do for _,e in ipairs(bySlot[player])do callbacks.input(player,e[1],e[2])end end
  callbacks.step()
 end
 function r:repair()
  if self.error or not self.dirty then return end
  local from=self.dirty;self.dirty=nil
  if not self.history[from] then fail('HISTORY_EXPIRED');return end
  callbacks.restore(self.history[from]);self.rollbacks=self.rollbacks+1
  for n=from,self.frame do simulate(n);self.replayed=self.replayed+1 end
 end
 function r:advance()
  self:repair();if self.error then return false end
  if self.frame-self.confirmed>=12 then self.stalled=true;return false end
  self.stalled=false
  local n=self.frame+1;self.localFrames[n]=encode(self.pending);self.pending={}
  simulate(n);self.frame=n
  local obsolete=n-120
  if obsolete>0 then self.history[obsolete]=nil;self.used[obsolete]=nil;self.remoteFrames[obsolete]=nil end
  -- Unacknowledged outgoing frames are retained, even during asymmetric delivery.
  for old in pairs(self.localFrames)do if old<=self.peerAck-24 then self.localFrames[old]=nil end end
  return true
 end
 function r:packet()
  if self.frame==0 then return nil end
  local first=math.max(1,math.min(self.peerAck+1,self.frame-5))
  local last=math.min(self.frame,first+23);local parts={}
  for n=first,last do if not self.localFrames[n] then fail('SEND_HISTORY_EXPIRED');return nil end;parts[#parts+1]=self.localFrames[n]end
  return first,self.confirmed,table.concat(parts,'|')
 end
 function r:receive(first,ack,payload)
  if self.error then return false end
  if type(first)~='number' or first~=math.floor(first) or first<1 or first>self.frame+240 or type(ack)~='number' or ack~=math.floor(ack) or ack<0 or ack>self.frame or type(payload)~='string' or #payload>8192 then return fail('BAD_PACKET')end
  local entries={};for s in string.gmatch(payload,'[^|]+')do entries[#entries+1]=s end
  if #entries<1 or #entries>24 or table.concat(entries,'|')~=payload then return fail('BAD_BATCH')end
  for _,s in ipairs(entries)do if not decode(s)then return fail('BAD_INPUT')end end
  self.peerAck=math.max(self.peerAck,ack)
  for i,s in ipairs(entries)do
   local n=first+i-1
   if n>self.confirmed then
    if self.remoteFrames[n] and self.remoteFrames[n]~=s then return fail('CONFLICTING_INPUT')end
    self.remoteFrames[n]=s
    if n<=self.frame and self.used[n]~=s then self.dirty=math.min(self.dirty or n,n)end
   end
  end
  while self.remoteFrames[self.confirmed+1] do self.confirmed=self.confirmed+1 end
  return true
 end
 return r
end
