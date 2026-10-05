import {readFileSync,writeFileSync} from 'node:fs';import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {renderPaintPng} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';
const out='outputs/duel-vnext',save=JSON.parse(readFileSync(out+'/fighter.save.json'));
const check=s=>{const r=s.playGet({view:true});assert.equal(r.logs.filter(l=>['error','lua-error'].includes(l.level)||/ERROR:/.test(l.text||'')).length,0,JSON.stringify(r.logs.slice(-6)));return r;};
const step=(s,n)=>{for(let i=0;i<n;i++)s.playStep(1/60,{observe:false});check(s);};
const click=(s,p,name)=>{s.playSetView(p);s.playClick(name,{observe:false});};
const node=(s,name)=>check(s).scene.nodes.find(n=>n.name===name);
const staged=createStudio(save);staged.playStart({playerCount:2});
for(let p=1;p<=2;p++)click(staged,p,'StartDuel');click(staged,2,'ReadyConfirm');step(staged,4);
click(staged,1,'SelectStage2');click(staged,1,'ReadyConfirm');step(staged,75);
assert.ok(node(staged,'ReadyConfirm')&&!node(staged,'Light'),'stale ready from old map must not start');
staged.playSetView(2);assert.equal(node(staged,'ReadyConfirmText').text,'确认准备','map change clears P2 ready');
click(staged,2,'ReadyConfirm');step(staged,180);assert.ok(node(staged,'Light'));assert.equal(node(staged,'StageTitle').text,'蒙德 · 城门大桥');
const fixture=structuredClone(save);fixture.assets.scripts[0].source+=`
local flowUpdate=OnUpdate
local injected=false
function OnUpdate(dt)
 flowUpdate(dt)
 if onlineReady and menuEpoch==1 and phase=='fight' then f[2].hp=0 end
 if onlineReady and menuEpoch>1 and not injected then
  injected=true
  local s=game.ServerSignal('FighterFrames');s:AddInt(3-seat);s:AddInt(99999999);s:AddInt(0);s:AddString('invalid');s:AddInt(1);s:SendSignal()
  print('OLD_SESSION_PACKET_SENT')
 end
end
`;
const match=createStudio(fixture);match.playStart({playerCount:2});for(let p=1;p<=2;p++){click(match,p,'StartDuel');click(match,p,'ReadyConfirm');}
step(match,550);assert.ok(node(match,'Rematch'),'match result missing');assert.equal(node(match,'ResultScore').text,'2 : 0 · 三局两胜');
let r=match.playGet({view:true,paint:true});writeFileSync(out+'/06-result.png',renderPaintPng(r.paint,r.canvasWidth,r.canvasHeight).data);
click(match,1,'Rematch');step(match,5);match.playSetView(2);assert.ok(node(match,'ReadyConfirm'),'peer must return to selection');
click(match,2,'ChooseKeqing');click(match,2,'ReadyConfirm');step(match,185);assert.ok(node(match,'Light'),'rematch did not start');
click(match,2,'DebugToggle');step(match,2);r=check(match);const diag=node(match,'BootDiagnostic').text;assert.ok(!diag.includes('错误'),'old-session packet reached new rollback session');assert.ok(r.logs.some(l=>l.text==='OLD_SESSION_PACKET_SENT'));
assert.ok(node(match,'Name2').text.startsWith('刻晴'),'reselection missing');assert.equal(node(match,'Status').text,'第 1 回合 | 0 - 0');
writeFileSync(out+'/flow-verification.json',JSON.stringify({simulatorVerified:true,deviceVerified:false,mapChangeInvalidatesReady:true,twoWinsMatchResult:true,rematchNeedsPeerReady:true,reselection:true,oldFramePacketIgnored:true},null,2));console.log('FLOW_PASS');
