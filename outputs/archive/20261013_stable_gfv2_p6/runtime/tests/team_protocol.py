"""New GF3 native-signal transport/server, isolated from old GFV2."""
from run import runtime,ROOT
rt=runtime(ROOT)
rt.execute('''
local Server=GF_REQUIRE('gf_team_server');local Transport=GF_REQUIRE('gf_team_selection')
local server=Server.new();local clients={};local handlers={{},{}};local now=0;local sent={}
local function deliver(outputs)
 for _,o in ipairs(outputs) do
  if o.signal=='GF3Progress' then assert(#o.params==5) end
  local cb=handlers[o.slot][o.signal];if cb then cb(nil,o.params) end
 end
end
for slot=1,2 do
 local game={ServerSignal=function(name)
  assert(name:sub(1,3)=='GF3');local values={}
  return {AddInt=function(_,v)values[#values+1]=v end,SendSignal=function()
   sent[#sent+1]={name=name,values=values};deliver(server:handle(name,values,2))
  end}
 end}
 local script={RegisterServerSignalHandler=function(_,name,cb)assert(name:sub(1,3)=='GF3');handlers[slot][name]=cb end}
 clients[slot]=Transport.new(game,script,function()return now end);clients[slot].start()
end
local function pump()now=now+.6;for _,c in ipairs(clients)do c.pump()end end
pump();assert(clients[1].slot==1 and clients[2].slot==2)
clients[1].publish({1,3,4},false);clients[2].publish({2,4,1},false);pump()
assert(clients[1].remoteCount==3 and not clients[1].reveal and not clients[2].reveal)
assert(#server:handle('GF3Team',{1,1,99,1,1,4,1},2)==0)
assert(#server:handle('GF3Team',{1,1,99,1,0,4,0},2)==0)
assert(#server:handle('GF3Team',{1,1,99,1,3,0,1},2)==0)
clients[1].publish({1,3,4},true);pump();assert(not clients[1].reveal)
clients[1].publish({1,3,4},false);pump();assert(not server.ready[1])
clients[1].publish({1,3,4},false);clients[2].publish({2,4,1},false);pump()
clients[1].publish({1,3,4},true);clients[2].publish({2,4,1},true);pump()
assert(server.locked and clients[1].reveal and clients[2].reveal)
assert(clients[2].reveal[1][2]==3)
local rev=server.revision[1]
assert(#server:handle('GF3Team',{1,server.epoch,rev,4,3,1,1},2)==0)
assert(#server:handle('GF3Team',{1,server.epoch,rev-1,1,3,4,0},2)==0)
clients[1].reveal=nil;pump();assert(clients[1].reveal,'reveal retry')
local oldEpoch=server.epoch;clients[1].reset();pump();assert(server.epoch==oldEpoch+1 and not server.locked)
assert(not clients[1].reveal and not clients[2].reveal and #clients[1].team==0)
assert(#server:handle('GF3Team',{1,1,100,1,3,4,1},2)==0)
assert(#server:handle('GF3Reset',{1,1},2)==0)
assert(#server:handle('GFV2Frames',{},2)==0)
''')
print('GF3 two clients: blind progress, ready/cancel, reveal retry, reset and stale packet checks PASS')
rt.execute('''
local callbacks={};local now=0
local game={ServerSignal=function()return {AddInt=function()end,SendSignal=function()end}end}
local script={RegisterServerSignalHandler=function(_,name,cb)callbacks[name]=cb end}
local t=GF_REQUIRE('gf_team_selection').new(game,script,function()return now end)
t.start();assert(t.publish({5,6,3},true) and not t.slot and t.ready)
callbacks.GF3Seat(nil,{2,1});assert(t.slot==2 and t.team[1]==5 and t.team[3]==3 and t.ready)
callbacks.GF3Seat(nil,{2,2});assert(#t.team==0 and not t.ready,'subsequent epoch change must clear old draft')
''')
print('Draft selection before seat and first-seat preservation PASS')
