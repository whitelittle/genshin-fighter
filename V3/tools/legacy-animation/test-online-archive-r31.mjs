import fs from 'node:fs';import assert from 'node:assert/strict';import {Worker} from 'node:worker_threads';import {createRequire} from 'node:module';import {renderScenePng} from '../vendor/simulator/studio/host-png.js';
const require=createRequire(import.meta.url),canvas=require.resolve('@napi-rs/canvas');
const project=JSON.parse(fs.readFileSync('dist/projects/raiden-nahida.json'));
project.assets.scripts[0].source=project.assets.scripts[0].source.replace("GF_FIRST_SCENE='intro'","GF_FIRST_SCENE='fight'");
project.assets.scripts[0].source=project.assets.scripts[0].source.replace("mode='demo',cpu={2,2}","mode='versus',cpu={false,2}");
project.assets.scripts[0].source+=`\nlocal prior=OnUpdate;local job;local started=false
function OnUpdate(dt)
 prior(dt)
 if not started and app and app.sceneName=='fight' and app.scene.state=='run' then
 started=true
local T=require('gf_transport');local clock=0;local handlers={{},{}};local pending={};local sockets={}
for id=1,2 do
 local game={ServerSignal=function(name)
  local args={};local b={};function b:AddInt(v) args[#args+1]=v end;function b:AddString(v) args[#args+1]=v end
  function b:SendSignal()
   if name=='GFV2Hello' then handlers[id].GFV2Seat(nil,{id})
   elseif name=='GFV2Frames' then pending[#pending+1]={to=3-id,params=args} end
  end;return b
 end}
 local script={RegisterServerSignalHandler=function(_,name,cb) handlers[id][name]=cb end}
 sockets[id]=T.new(game,script,function() return clock end);sockets[id].start();sockets[id].pump()
 assert(sockets[id].slot==id and sockets[id].diag.hello==1,'seat handshake')
end
local pkt={};for i=1,24 do pkt[i]=0 end;pkt[1]=-7201;pkt[3]=19
sockets[1].send(pkt);assert(#pending==1);handlers[2].GFV2FramesOut(nil,pending[1].params)
assert(sockets[2].diag.accepted==1 and sockets[2].packets[1][3]==19,'frame transport');handlers[2].GFV2FramesOut(nil,{1,19,0,'malformed',1});assert(sockets[2].diag.rejected==1,'invalid packet accepted')
print('NET GFV2 TRANSPORT PASS seats 1/2, 24-word packet forwarding and validation')

local results={(function(...)

local latency, jitter, loss, frames, seed = ...
local O = require('gf_online')
local N = require('gf_net')
local Sim = require('gf_sim')
local R = require('gf_roster')

local rng = seed
local function rand() rng = (rng * 1103515245 + 12345) & 0x7fffffff; return rng / 0x7fffffff end

local now = 0
local level = {}                    -- relay output: Level custom variables
local queue = {}                    -- packets in flight {at, slot, list}
local players = {{nonce = 111, slot = 1}, {nonce = 222, slot = 2}}

local function makeIo(i)
    local dirty = {}
    return {
        dirty = dirty,
        player = function(name)
            if name == 'GF_NONCE' then return players[i].nonce end
            if name == 'GF_SLOT' then return players[i].slot end
        end,
        level = function(name) return level[name] end,
        send = function(list)
            if rand() < loss then return end
            local copy = {}
            for k = 1, #list do copy[k] = list[k] end
            queue[#queue + 1] = {at = now + latency + rand() * jitter, slot = i, list = copy}
        end,
        now = function() return now end,
    }
end

local clients = {O.new(makeIo(1)), O.new(makeIo(2))}
level.GF_SLOTS = {8, 1, 1, 0, 0, 0, 0, 0, 0}
clients[1].me.char, clients[2].me.char = 1, 2
clients[1].me.selecting=true;clients[2].me.selecting=true
clients[1].host.stage = 2

local function makeSimOpts(chars, setup, sd)
    return {chars = {R[chars[1]], R[chars[2]]}, rounds = setup.rounds, time = setup.time, seed = sd}
end

local inLog, hashAt, logged = {}, {}, 0
local masks = {0, 0}
local hold = {0, 0}
local started = {false, false}
for tick = 1, frames do

    now = now + 1 / 60
    -- deliver
    local keep = {}
    for _, p in ipairs(queue) do
        if p.at <= now then
            -- relay: nonce is replaced by 0 is not needed here; slot from the sender
            level['GF_IN_' .. p.slot] = p.list
            for _, c in ipairs(clients) do c.dirty[p.slot] = true end
        else keep[#keep + 1] = p end
    end
    queue = keep
    for i, c in ipairs(clients) do
        O.poll(c)
        if not c.match then
            c.me.ready = true
            O.lobbyTick(c)
            if O.isHost(c) then O.hostStart(c, nil, makeSimOpts) else O.checkJoin(c, nil, makeSimOpts) end
            if c.match then started[i] = tick end
        else
            hold[i] = hold[i] - 1
            if hold[i] <= 0 then
                hold[i] = 1 + math.floor(rand() * 14)
                local m = 0
                for b = 0, 9 do if rand() < 0.18 then m = m | (1 << b) end end
                if m & 12 == 12 then m = m & ~4 end
                masks[i] = m
            end
            O.matchStep(c, masks[i])
            if i == 1 then
                -- log confirmed inputs and the confirmed state's hash (the session prunes both)
                local n = c.match.session
                for f = (logged or 0) + 1, n.confirmed do
                    inLog[f] = {n.inputs[1][f] or 0, n.inputs[2][f] or 0}
                    logged = f
                end
                if n.snaps[n.confirmed] then hashAt[n.confirmed] = n.snaps[n.confirmed]:hash() end
            end
        end
    end
end
-- let the last packets arrive and settle (no new frames)
for settle = 1, 120 do

    now = now + 1 / 60
    local keep = {}
    for _, p in ipairs(queue) do
        if p.at <= now then level['GF_IN_' .. p.slot] = p.list; for _, c in ipairs(clients) do c.dirty[p.slot] = true end
        else keep[#keep + 1] = p end
    end
    queue = keep
    for _, c in ipairs(clients) do
        O.poll(c)
        if c.match then
            local n = c.match.session
            O.send(c, N.packet(n, {match = c.match.id, lobby = O.lobbyWord(c.me.char, true)}))
            N.settle(n)
        end
    end
end

local a, b = clients[1].match, clients[2].match
if not a or not b then return 'nomatch', started[1], started[2] end
local na, nb = a.session, b.session
-- compare confirmed hashes at common frames
local common, diff = 0, 0
for f, h in pairs(na.myHash) do
    local h2 = nb.myHash[f]
    if h2 then common = common + 1; if h2 ~= h then diff = diff + 1 end end
end
-- reference: replay the inputs both sides agree on, locally
local upto = 0
for f in pairs(hashAt) do if f > upto then upto = f end end
local ref = Sim.new(makeSimOpts(a.roster.chars, a.setup, a.seed))
local refOk = true
for f = 1, upto do

    ref:step(inLog[f][1], inLog[f][2])
    if hashAt[f] and hashAt[f] ~= ref:hash() then refOk = false end
end
return 'ok', a.id == b.id, common, diff, na.desync and na.desync.frame or 0, nb.desync and nb.desync.frame or 0,
       refOk, upto, na.stats.rollbacks, na.stats.maxRollback, na.stats.stalls, nb.stats.rollbacks, a.side, b.side

end)(0.05,0.025,0.02,1800,9)}
assert(results[1]=='ok' and results[2] and results[3]>=3 and results[4]==0 and results[5]==0 and results[6]==0 and results[7] and results[8]>1200,'rollback consistency');print('GFTEST PASS GFV2 two clients same match, both sides, loss/jitter, confirmed hashes, deterministic replay')
end
end
`;
const worker=new Worker(`const {parentPort}=require('node:worker_threads');globalThis.OffscreenCanvas=function(w,h){return require(${JSON.stringify(canvas)}).createCanvas(w,h)};globalThis.postMessage=v=>parentPort.postMessage(v);let q=[];parentPort.on('message',data=>globalThis.onmessage?globalThis.onmessage({data}):q.push(data));import(${JSON.stringify('file://'+process.cwd()+'/dist/editor/simulator-worker.js')}).then(()=>{for(const data of q)globalThis.onmessage({data})});`,{eval:true});
let seq=0;const pending=new Map();worker.on('message',r=>{const p=pending.get(r.id);if(!p)return;pending.delete(r.id);r.ok?p.resolve(r.value):p.reject(Error(r.error));});worker.on('error',e=>{for(const p of pending.values())p.reject(e);});
const call=(action,body={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});worker.postMessage({id,action,body});});
let logs=[];async function observe(){const s=await call('play',{action:'get',args:{view:true,compact:true}});assert.equal(s.mountError,null);const errors=s.logs.filter(l=>(l.level==='error'||l.level==='lua-error'));assert.equal(errors.length,0,JSON.stringify(errors));logs=s.logs;return s;}
async function step(n){for(let i=0;i<n;i++)await call('play',{action:'step',args:{dt:1/60,light:true}});}
async function capture(name){const s=await observe();const im=renderScenePng(s.scene,s.canvasWidth,s.canvasHeight);fs.mkdirSync('verification/dual-character',{recursive:true});fs.writeFileSync('verification/dual-character/'+name+'.png',im.data);return s;}
try{await call('import',{format:'json',filename:'raiden-nahida.json',data:Buffer.from(JSON.stringify(project)).toString('base64')});await call('play',{action:'start'});await call('play',{action:'pause'});for(let i=0;i<160;i++){await step(10);await observe();if(logs.some(l=>l.text.includes('GFTEST PASS GFV2')))break;}let s=await observe();assert(logs.some(l=>l.text.includes('GFTEST PASS')),JSON.stringify(logs.slice(-5)));fs.mkdirSync('verification/online-archive-r31',{recursive:true});fs.writeFileSync('verification/online-archive-r31/report.json',JSON.stringify({checks:logs.filter(l=>l.text.startsWith('NET GFV2')||l.text.includes('GFTEST')).map(l=>l.text),method:'Actual Lua GFV2 transport serialization and validation; two rollback clients through simulated latency, jitter and packet loss with deterministic replay'},null,2));console.log(logs.filter(l=>l.text.includes('GFTEST PASS')||l.text.startsWith('NET GFV2')).map(l=>l.text).join('\n'));
}finally{await worker.terminate();}
