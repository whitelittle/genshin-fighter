import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const profile=process.argv[2]||'light';assert.ok(['light','minimum'].includes(profile));
const diagnostic=process.argv.includes('--diagnostic');
const out=`outputs/demo-online-${profile}-rollback${diagnostic?'-diagnostic':''}`;mkdirSync(out,{recursive:true});
let source=readFileSync('work/demo-online.lua','utf8');
source=source.replace('intermission=0;acc=0;input=', 'intermission=0;input=');
const inputStart=source.indexOf('local function applyInput('),inputEnd=source.indexOf('local function sendInput(',inputStart);
const apply=source.slice(inputStart,inputEnd).replace('spriteCache={};','');
const core=source.slice(0,source.indexOf('local spriteData=')).replace('local publishState','local publishState\nlocal replaying=false\nlocal originalPrint=print\nlocal function print(...)if not replaying then originalPrint(...)end end');
const callbacks=`
local function copy(value,seen)
 if type(value)~='table' then return value end
 seen=seen or {};if seen[value]then return seen[value]end
 local result={};seen[value]=result;for key,v in pairs(value)do result[key]=copy(v,seen)end;return result
end
local function capture()
 return copy({f=f,controls=controls,input=input,directions=directions,lastDirection=lastDirection,motionMove=motionMove,heldButtons=heldButtons,controlPlayer=controlPlayer,tick=tick,phase=phase,round=round,wins=wins,remaining=remaining,freeze=freeze,intermission=intermission,stage=stage,roleChoice=roleChoice})
end
local function restore(snapshot)
 local s=copy(snapshot);f=s.f;controls=s.controls;input=s.input;directions=s.directions;lastDirection=s.lastDirection;motionMove=s.motionMove;heldButtons=s.heldButtons;controlPlayer=s.controlPlayer;tick=s.tick;phase=s.phase;round=s.round;wins=s.wins;remaining=s.remaining;freeze=s.freeze;intermission=s.intermission;stage=s.stage;roleChoice=s.roleChoice
end
`;
writeFileSync('work/rollback-game-core.lua',core+apply+callbacks);
source=source.slice(0,source.indexOf('local function sendInput('));
// Replace legacy host snapshot publishing with frame input journals.
source=source.replace(/publishState=function\(\)[\s\S]*?\nend\nlocal function applyInput/, 'publishState=function()end\nlocal function applyInput');
source=source.replace('spriteCache={};restart();','restart();');
source=source.replace('local publishState','local publishState\nlocal replaying=false\nlocal originalPrint=print\nlocal function print(...)if not replaying then originalPrint(...)end end');
source+=callbacks+readFileSync('work/rollback-session.lua','utf8')+`
local rb=nil
local function sendInput(event,value)
 if onlineReady and rb then rb:queue(event,value)end
end
local function flushFrames()
 if not rb or rb.error then return end
 local first,ack,payload=rb:packet();if not first then return end
 local sig=game.ServerSignal('FighterFrames');sig:AddInt(seat);sig:AddInt(first);sig:AddInt(ack);sig:AddString(payload);sig:SendSignal()
end
function OnStart()
 script:RegisterServerSignalHandler('FighterFramesOut',function(_,params)
  if not rb or tonumber(params[1])~=3-seat then return end
  rb:receive(tonumber(params[2]),tonumber(params[3]),params[4])
 end)
 script:RegisterServerSignalHandler('FighterJoined',function()
  if onlineReady or (seat~=1 and seat~=2)then return end
  onlineReady=true;restart();acc=0
  rb=NewRollbackSession({capture=capture,restore=restore,input=applyInput,step=step},seat)
 end)
 script:RegisterServerSignalHandler('FighterSeat',function(_,params)
  local assigned=tonumber(params[1]);if assigned~=1 and assigned~=2 then return end
  if onlineReady then return end
  seat=assigned
  if seat==2 and not joined then joined=true;game.ServerSignal('FighterJoin'):SendSignal()end
 end)
`;
const original=readFileSync('work/demo-online.lua','utf8');
const binds=original.slice(original.indexOf(" bind('KeyboardMoveLeftKeyDown'"),original.indexOf('\nfunction OnDisable()'));
source+=binds;
source+=`
local resendTime=0
function OnUpdate(dt)
 if not onlineReady or not rb then return end
 replaying=true;rb:repair();replaying=false
 acc=math.min(acc+math.min(dt,.1),.1);local n=0
 while acc>=1/60 and n<6 do
  if not rb:advance()then acc=0;break end
  acc=acc-1/60;n=n+1
 end
 resendTime=resendTime+dt
 if resendTime>=.05 then resendTime=0;flushFrames()end
 draw()
 stats.text=stats.text..' | 回滚 '..rb.rollbacks..' / 网络帧 '..rb.frame
 if rb.error then status.text='联机错误：'..rb.error
 elseif rb.stalled then status.text='等待远端输入 · 暂停预测'end
end
function OnDisable()
 if rb then for _,key in ipairs({'left','right','down','block','light','heavy'})do rb:queue(key,0)end;rb:queue('stick',5);flushFrames()end
end
`;
// Device-compatible boot wrapper is retained from the successful import-fix package.
const previous=readFileSync('outputs/demo-online-light-importfix/fighter-中文源稿.lua','utf8');
source+=previous.slice(previous.indexOf('\nlocal bootOK=false'));
if(diagnostic){
 source=source.replace('local rb=nil',"local rb=nil\nlocal debugNet={tx=0,bytes=0,last='等待启动',previous='',updates=0}");
 source=source.replace('sig:AddString(payload);sig:SendSignal()',"sig:AddString(payload);sig:SendSignal();debugNet.tx=debugNet.tx+1;debugNet.bytes=#payload");
 source=source.replace("game.ServerSignal('FighterHello'):SendSignal()",'helloRequest()').replace("game.ServerSignal('FighterJoin'):SendSignal()",'joinRequest()');
 source=source.replace('function OnStart()',`
local helloCount,joinCount,handshakeTime,receiveCount=0,0,0,0
local function helloRequest()
 helloCount=helloCount+1
 debugNet.last='调用 Hello 发送'
 if helloCount<=3 or helloCount%10==0 then print('[NET CLIENT] Hello SEND '..helloCount)end
 game.ServerSignal('FighterHello'):SendSignal()
end
local function joinRequest()
 joinCount=joinCount+1
 debugNet.last='调用 Join 发送'
 if joinCount<=3 or joinCount%10==0 then print('[NET CLIENT] Join SEND '..joinCount)end
 game.ServerSignal('FighterJoin'):SendSignal()
end
function OnStart()`);
 source=source.replace('seat=assigned',"seat=assigned;debugNet.last='收到席位 '..seat;print('[NET CLIENT] Seat RECEIVED '..seat)");
 source=source.replace('onlineReady=true;restart();acc=0',"debugNet.last='收到开战通知';print('[NET CLIENT] Joined RECEIVED');onlineReady=true;restart();acc=0");
 source=source.replace('rb:receive(tonumber(params[2]),tonumber(params[3]),params[4])',"receiveCount=receiveCount+1;debugNet.last='收到输入批次';if receiveCount==1 then print('[NET CLIENT] FramesOut RECEIVED')end;rb:receive(tonumber(params[2]),tonumber(params[3]),params[4])");
 source=source.replace('function OnUpdate(dt)\n if not onlineReady',`function OnUpdate(dt)
 handshakeTime=handshakeTime+dt
 debugNet.updates=debugNet.updates+1
 if handshakeTime>=1 then
  handshakeTime=0
  if not onlineReady then if seat==2 then joinRequest()else helloRequest()end end
  local label=root:FindChild('BootDiagnostic')
  local state=not onlineReady and (seat==0 and '等待席位回包' or (seat==1 and '已登记，等待另一人/开战' or '等待开战回包')) or (rb.error and ('错误 '..rb.error)or (rb.stalled and '等待远端输入' or '战斗运行'))
  if label then label.text='DEBUG / Lua 已启动 · 更新次数 '..debugNet.updates..'\\n'..state..' | 席位 '..seat..'\\nHello 调用 '..helloCount..' | Join 调用 '..joinCount..'\\n输入发送 '..debugNet.tx..' | 收到 '..receiveCount..' | 批次字节 '..debugNet.bytes..'\\n网络帧 '..(rb and rb.frame or 0)..' | 远端确认 '..(rb and rb.confirmed or 0)..' | 对方确认 '..(rb and rb.peerAck or 0)..'\\n回滚 '..(rb and rb.rollbacks or 0)..' | 重算帧 '..(rb and rb.replayed or 0)..'\\n最近：'..debugNet.last end
  if debugNet.previous~=state then debugNet.previous=state;print('[NET CLIENT] STATE '..state)end
 end
 if not onlineReady`);
}
writeFileSync('work/demo-online-rollback.lua',source);
function deviceLua(s){
 s=s.replace(/^\uFEFF/,'').replace(/\r\n?/g,'\n');let result='',i=0;
 while(i<s.length){if(s.slice(i,i+2)==='--'){while(i<s.length&&s[i]!=='\n')i++;continue;}
 if(s[i]==="'"||s[i]==='"'){const q=s[i++];result+=q;while(i<s.length){const ch=s[i++];if(ch==='\\'){result+=ch+s[i++];continue;}if(ch===q){result+=ch;break;}result+=ch.charCodeAt(0)>127?[...Buffer.from(ch)].map(b=>'\\'+String(b).padStart(3,'0')).join(''):ch;}}
 else result+=s[i++];}assert.ok(!/[^\x09\x0a\x20-\x7e]/.test(result));return result;
}
const save=JSON.parse(readFileSync('outputs/demo-online-light-importfix/fighter.save.json','utf8'));
save.assets.server.root.name=diagnostic?'FighterOnlineRollbackDebug':(profile==='light'?'FighterOnlineRollbackTest':'FighterOnlineRollbackSmall');save.meta.name=save.assets.server.root.name;save.assets.server.meta.name=save.meta.name;
const script=save.assets.scripts[0];
if(diagnostic){
 const label=save.assets.server.root.children[0].children.find(n=>n.name==='BootDiagnostic');label.fontSize=13;label.text='DEBUG / 等待 Lua 启动';
 for(const transform of Object.values(label.transformByPlatform)){transform.offset={x:400,y:65};transform.size={x:450,y:175};}
}
const profileSave=JSON.parse(readFileSync(`outputs/demo-online-${profile}/fighter.save.json`,'utf8'));
const old=profileSave.assets.scripts[0].source;
if(profile==='minimum'){
 const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean);
 for(const role of ['Keqing','Diluc'])find(find(save.assets.server.root,role),'Sprite').children=structuredClone(find(find(profileSave.assets.server.root,role),'Sprite').children);
 let nextGuid=1073741850,nextId=0;const walk=n=>{n.guid=nextGuid++;n.id='rollback_small_'+(++nextId);delete n.giaRelatedGuids;delete n.giaInfoIndex;delete n.scriptMappingIds;for(const c of n.children||[])walk(c);};
 walk(save.assets.server.root);if(save.assets.client?.root)walk(save.assets.client.root);
 script.guid=nextGuid++;script.id=String(script.guid);script.controlId=save.assets.server.root.children[0].id;
 save.assets.server.meta.giaFileId=save.assets.server.root.guid;
}
const start=old.indexOf('local spriteData=')+'local spriteData='.length,end=old.indexOf('\nlocal spriteCache=',start);
source=source.replace('SPRITE_DATA',old.slice(start,end)).replaceAll('SPRITE_POOL',profile==='minimum'?'939':'2275');
writeFileSync(out+'/fighter-中文源稿.lua',source);script.source=deviceLua(source);script.path=diagnostic?'lua/fighter_online_rollback_debug.lua':(profile==='light'?'lua/fighter_online_rollback.lua':'lua/fighter_online_rollback_small.lua');
save.serverLogic={version:1,rules:[
 {id:'seats',signalName:'FighterHello',actions:[{kind:'sendClientScriptSignal',target:'Player1',signalName:'FighterSeat',params:[1]},{kind:'sendClientScriptSignal',target:'Player2',signalName:'FighterSeat',params:[2]}]},
 {id:'join',signalName:'FighterJoin',actions:[{kind:'sendClientScriptSignal',target:'AllPlayers',signalName:'FighterJoined',params:[]}]},
 {id:'frames',signalName:'FighterFrames',actions:[{kind:'sendClientScriptSignal',target:'AllPlayers',signalName:'FighterFramesOut',params:[0,1,2,3].map(fromSignalParam=>({fromSignalParam}))}]}]};
// Retain the simulator's existing save-level location of serverLogic.
const oldLogic=JSON.parse(readFileSync('outputs/demo-online-light/server-logic.json','utf8'));
if(save.assets.serverLogic){delete save.assets.serverLogic;}
writeFileSync(out+'/fighter.lua',script.source);writeFileSync(out+'/fighter.save.json',JSON.stringify(save));writeFileSync(out+'/server-logic.json',JSON.stringify(save.serverLogic,null,2));
const ex=createStudio(save).exportData('gia-combined'),buffer=Buffer.from(ex.data,ex.encoding);assert.ok(validateServerGiaCompatibility(buffer).valid);
const stamp=new Date().toLocaleString('sv-SE',{timeZone:'Asia/Hong_Kong'}).replace(/[-: ]/g,'');
const filename='gpt_'+stamp.slice(0,8)+'_'+stamp.slice(8,12)+'_原神格斗_双人_'+(diagnostic?'回滚握手诊断':(profile==='minimum'?'容量精简回滚':'回滚测试'))+'.gia';writeFileSync(out+'/'+filename,buffer);
writeFileSync(out+'/build.json',JSON.stringify({filename,template:save.meta.name,scriptPath:script.path,profile,giaBytes:buffer.length,predictionLimit:12,historyFrames:120,resendSeconds:.05,maximumBatchFrames:24,deviceVerified:false},null,2));
console.log(filename);
