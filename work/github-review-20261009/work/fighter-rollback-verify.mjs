import {readFileSync,writeFileSync} from 'node:fs';import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
const out=`outputs/demo-online-${process.argv[2]||'light'}-rollback${process.argv.includes('--diagnostic')?'-diagnostic':''}`,save=JSON.parse(readFileSync(out+'/fighter.save.json'));
const module=readFileSync('work/rollback-session.lua','utf8'),core=readFileSync('work/rollback-game-core.lua','utf8');
const tests=module+`
local function NewGame()
${core}
 replaying=true;restart()
 return {capture=capture,restore=restore,input=applyInput,step=step}
end
local function canonical(v)
 if type(v)~='table'then return type(v)=='number' and string.format('%.17g',v)or tostring(v)end
 local keys={};for k in pairs(v)do keys[#keys+1]=k end
 table.sort(keys,function(a,b)return tostring(a)<tostring(b)end)
 local result={};for _,k in ipairs(keys)do result[#result+1]=tostring(k)..'='..canonical(v[k])end
 return '{'..table.concat(result,';')..'}'
end
local function event(g,s)
 if s=='-'then return end
 for item in string.gmatch(s,'[^,]+')do local name,value=string.match(item,'^([%a]+):(%d+)$');g.input(1,name,tonumber(value))end
end
local function run(delayed)
 local games,peers,record,transit={NewGame(),NewGame()},{},{{},{}},{}
 for i=1,2 do peers[i]=NewRollbackSession(games[i],i)end
 local function packet(i,t,drain)
  local first,ack,payload=peers[i]:packet();if not first then return end
  -- Deterministic loss, jitter and duplicate packets, including bursts.
  if delayed and not drain and (t%17==0 or (t%103>=95))then return end
  local delay=delayed and not drain and (4+(t*7+i*3)%7)or 0
  transit[#transit+1]={due=t+delay,target=3-i,first=first,ack=ack,payload=payload}
  if delayed and t%31==0 then transit[#transit+1]={due=t+delay+2,target=3-i,first=first,ack=ack,payload=payload}end
 end
 local function deliver(t)
  -- Reverse delivery order intentionally reorders equal-time packets.
  for n=#transit,1,-1 do local p=transit[n];if p.due<=t then assert(peers[p.target]:receive(p.first,p.ack,p.payload),peers[p.target].error);table.remove(transit,n)end end
  for i=1,2 do peers[i]:repair();assert(not peers[i].error,peers[i].error)end
 end
 local schedule={
  [1]={{1,'clickLight',1}},[20]={{2,'clickHeavy',1}},
  [80]={{1,'right',1},{2,'left',1}},[95]={{1,'right',0},{2,'left',0}},
  [115]={{1,'down',1},{1,'right',1},{1,'down',0},{1,'right',0},{1,'clickLight',1}},
  [180]={{2,'left',1},{2,'left',0},{2,'down',1},{2,'left',1},{2,'clickHeavy',1},{2,'down',0},{2,'left',0}},
  [245]={{1,'jump',1}},[290]={{2,'block',1}},[340]={{2,'block',0}},
  [370]={{2,'role',1}},[410]={{1,'stage',3}},[440]={{1,'restart',1}},[470]={{1,'clickHeavy',1}},[500]={{2,'clickLight',1}}
 }
 local sawImmediate=false;local stalls=0
 for t=1,600 do
  deliver(t)
  for _,e in ipairs(schedule[t]or {})do peers[e[1]]:queue(e[2],e[3])end
  for i=1,2 do
   if peers[i]:advance()then record[i][peers[i].frame]=peers[i].localFrames[peers[i].frame]else stalls=stalls+1 end
   if t==1 and i==1 then sawImmediate=games[1].capture().f[1].attack~=nil end
  end
  if t%3==0 then for i=1,2 do packet(i,t,false)end end
 end
 -- Stop new input, align clocks, retransmit, then compare confirmed states at one frame.
 for t=601,680 do
  deliver(t)
  local low=peers[1].frame<peers[2].frame and 1 or (peers[2].frame<peers[1].frame and 2 or 0)
  if low>0 and peers[low]:advance()then record[low][peers[low].frame]=peers[low].localFrames[peers[low].frame]end
  for i=1,2 do packet(i,t,true)end
 end
 deliver(1000)
 assert(peers[1].frame==peers[2].frame,'clock convergence')
 assert(peers[1].confirmed>=peers[1].frame and peers[2].confirmed>=peers[2].frame,'not confirmed')
 assert(canonical(games[1].capture())==canonical(games[2].capture()),'peer full state mismatch')
 local reference=NewGame()
 for n=1,peers[1].frame do
  for i=1,2 do for item in string.gmatch(record[i][n]or '-','[^,]+')do
   if item~='-'then local name,value=string.match(item,'^([%a]+):(%d+)$');reference.input(i,name,tonumber(value))end
  end end
  reference.step()
 end
 assert(canonical(reference.capture())==canonical(games[1].capture()),'reference deterministic replay mismatch')
 assert(sawImmediate,'local input waited for network')
 if delayed then assert(peers[1].rollbacks+peers[2].rollbacks>0,'rollback never triggered')end
 print('ROLLBACK_PASS '..tostring(delayed)..' frames='..peers[1].frame..' rollbacks='..(peers[1].rollbacks+peers[2].rollbacks)..' stalls='..stalls)
end
function OnStart()
 run(false);run(true)
 local g1,g2=NewGame(),NewGame()
 for _,g in ipairs({g1,g2})do local snapshot=g.capture();snapshot.f[1].meter=100;g.restore(snapshot)end
 local x,y=NewRollbackSession(g1,1),NewRollbackSession(g2,2)
 for n=1,2 do for _,e in ipairs({{'down',1},{'right',1},{'down',0},{'right',0}})do x:queue(e[1],e[2])end end
 x:queue('clickHeavy',1)
 for n=1,10 do assert(x:advance());assert(y:advance())end
 local first,ack,payload=x:packet();assert(y:receive(first,ack,payload));y:repair()
 first,ack,payload=y:packet();assert(x:receive(first,ack,payload));x:repair()
 for n=11,24 do
  assert(x:advance());assert(y:advance())
  first,ack,payload=x:packet();assert(y:receive(first,ack,payload))
  first,ack,payload=y:packet();assert(x:receive(first,ack,payload))
  x:repair();y:repair()
 end
 assert(g1.capture().f[2].hp==62 and g1.capture().f[1].meter>34 and g1.capture().f[1].meter<36,'super rollback damage/meter')
 assert(canonical(g1.capture())==canonical(g2.capture()),'super rollback full state')
 print('ROLLBACK_SUPER_PASS')
 local g=NewGame();local r=NewRollbackSession(g,1)
 for n=1,12 do assert(r:advance())end
 assert(not r:advance()and r.frame==12,'prediction limit')
 assert(not r:receive(1,0,'light:999'),'invalid packet accepted')
 print('ROLLBACK_GUARDS_PASS')
end
`;
const testSave=structuredClone(save);testSave.assets.scripts[0].source=tests;testSave.serverLogic={version:1,rules:[]};
const test=createStudio(testSave);test.playStart();const state=test.playGet({view:true});
const errors=state.logs.filter(l=>['error','lua-error'].includes(l.level));assert.equal(errors.length,0,JSON.stringify(errors));
const messages=state.logs.map(l=>l.text);assert.equal(messages.filter(s=>s?.includes('ROLLBACK_PASS')).length,2,JSON.stringify(messages));assert.ok(messages.some(s=>s?.includes('ROLLBACK_GUARDS_PASS')));
assert.ok(messages.some(s=>s?.includes('ROLLBACK_SUPER_PASS')));
// Full production UI/script integration, with independent simulator clients.
const s=createStudio(save);s.playStart({playerCount:2});s.playSetView(1);s.playClick('Light',{observe:false});
for(let n=0;n<30;n++)s.playStep(1/60,{observe:false});
s.playSetView(2);s.playClick('Heavy',{observe:false});for(let n=0;n<80;n++)s.playStep(1/60,{observe:false});
for(let n=0;n<12;n++)s.playStep(1/60,{observe:false});
const a=s.playSetView(1,{view:true}),b=s.playSetView(2,{view:true});
if(process.argv.includes('--diagnostic')){
 assert.ok(a.scene.nodes.find(n=>n.name==='BootDiagnostic').text.includes('回滚'));
 const disconnected=structuredClone(save);disconnected.serverLogic={version:1,rules:[]};const waiting=createStudio(disconnected);waiting.playStart();
 for(let n=0;n<70;n++)waiting.playStep(1/60,{observe:false});
 const diagnosticState=waiting.playGet({view:true});const diagnosticText=diagnosticState.scene.nodes.find(n=>n.name==='BootDiagnostic').text;
 assert.ok(diagnosticText.includes('等待席位回包')&&diagnosticText.includes('Hello 调用 2'),diagnosticText);
 assert.ok(diagnosticState.logs.some(l=>String(l.text).includes('Hello SEND 2')),'Hello retry missing');
}
for(const v of [a,b])assert.equal(v.logs.filter(l=>['error','lua-error'].includes(l.level)||String(l.text).includes('ERROR:')).length,0,JSON.stringify(v.logs.slice(-8)));
for(const name of ['Hp1','Hp2','Keqing','Diluc','Timer'])assert.deepEqual(a.scene.nodes.find(n=>n.name===name),b.scene.nodes.find(n=>n.name===name),name+' UI mismatch');
assert.ok(a.scene.nodes.find(n=>n.name==='Stats').text.includes('生命 75 / 92'),'both players did not hit');
const report={simulatorVerified:true,deviceVerified:false,coreTests:messages.filter(s=>s?.includes('ROLLBACK_')),tests:{actualCombatStateReplay:true,localAttackWithoutRemoteReply:true,lateInputRollback:true,reorderedPackets:true,duplicatePackets:true,lossAndRetransmission:true,fullStateMatchesReference:true,roleStageRestartReplay:true,predictionLimit:true,invalidPacketRejected:true,twoRuntimeUIBoot:true}};
writeFileSync(out+'/verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
