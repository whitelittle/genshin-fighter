import fs from 'node:fs';import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {renderPaintPng} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';
const out=process.env.LOADING_FIX_VERIFY_OUT||'outputs/loading-fix-20261005',save=JSON.parse(fs.readFileSync(out+'/simulator.save.json'));
const scenarios=[];
function check(s){const r=s.playGet({view:true});const errors=r.logs.filter(l=>['error','lua-error'].includes(l.level)||/RESOURCE ERROR|ERROR:/.test(l.text||''));assert.equal(errors.length,0,JSON.stringify(errors));return r;}
function step(s,n,dt=1/60){for(let i=0;i<n;i++)s.playStep(dt,{observe:false});return check(s);}
function has(s,n){return check(s).scene.nodes.some(x=>x.name===n);}
function until(s,p,label,max=18000){for(let i=0;i<max;i+=20){if(p())return;step(s,20);}throw Error('Timeout '+label+JSON.stringify(check(s).logs.slice(-4)));}
function snap(s,n){if(process.env.VERIFY_SKIP_PAINT==='1')return;const r=s.playGet({view:true,paint:true});fs.writeFileSync(out+'/'+n+'.png',renderPaintPng(r.paint,r.canvasWidth,r.canvasHeight).data);}
// Delay peer readiness at the real resource gate. The release below only tests display handoff;
// the separate two-player scenario exercises real GF10 ready/join signaling.
const wait=structuredClone(save);wait.assets.scripts[0].source+=`
local probeUpdate=OnUpdate
local probeStarted=false
function OnUpdate(dt)
 probeUpdate(dt)
 if not probeStarted and loadingState=='ready' then
  probeStarted=true;teamChoice={{1,3,5},{2,4,6}};roleChoice={1,2};menuMode='roundload';menuReady={true,true};menuLoaded={false,false};menuDirty=true
  resourceGate.request('battle',roleChoice)
 end
 if probeStarted and loadingState=='ready' and menuMode=='roundload' then
  resourceGate.loader.probeWait=(resourceGate.loader.probeWait or 0)+1
  if resourceGate.loader.probeWait==300 then menuMode='battle';menuDirty=true;menuDraw();resourceGate.loader.syncCover()end
 end
end`;
const w=createStudio(wait);w.playStart();until(w,()=>check(w).logs.some(l=>/LOAD SCHEDULE/.test(l.text||''))&&has(w,'LoadingBar')&&!has(w,'StartDuelHit'),'wait gate');
until(w,()=>check(w).logs.filter(l=>/LOAD SCHEDULE/.test(l.text||'')).length>=2,'battle resources complete');
assert(has(w,'LoadingBlack'));if(process.env.VERIFY_ALLOW_DIAG_TEXT!=='1')assert(!has(w,'LoadingText'));assert(!has(w,'LoadingPaimon'));step(w,100);assert(has(w,'LoadingBar'));snap(w,'waiting-local-ready');
until(w,()=>has(w,'Timer')&&!has(w,'LoadingBar'),'display ownership handoff');snap(w,'battle-display-handoff');w.playStop();console.log('WAIT_HANDOFF_PASS');scenarios.push('local ready keeps cover until battle display handoff; peer wait injected');
for(const canvasId of ['pc-16-9','mobile-19.5-9']){
 const s=createStudio(save);s.playStart({canvasId});const r=check(s),back=r.scene.nodes.find(n=>n.name==='FullscreenBacking')||r.scene.nodes.find(n=>n.name==='LoadingBlack');assert(back);assert(back.sourceWidth>=r.canvasWidth);assert(back.sourceHeight>=r.canvasHeight);if(process.env.VERIFY_ALLOW_DIAG_TEXT!=='1')assert(!has(s,'LoadingText'));if(process.env.VERIFY_COVER_MARGIN==='1')assert(back.sourceWidth>=r.canvasWidth*1.9,'cover must overhang both sides: '+back.sourceWidth+'/'+r.canvasWidth);until(s,()=>has(s,'StartDuel')&&!has(s,'LoadingBar'),'home');assert(has(s,'FullscreenBacking'));snap(s,canvasId+'-home');s.playStop();console.log('CANVAS_HOME_PASS',canvasId);scenarios.push(canvasId+' loading cover / home backing covers simulator canvas; home exits loading');
}
const flow=structuredClone(save);flow.assets.scripts[0].source+=`
local testUpdate=OnUpdate
function OnUpdate(dt)testUpdate(dt);if onlineReady and phase=='fight' and tick>250 and menuEpoch<5 then f[round==2 and 1 or 2].hp=0 end end`;
const s=createStudio(flow);s.playStart({playerCount:2});
const settled=()=>until(s,()=>!has(s,'LoadingBar'),'settle');
const click=(p,n)=>{s.playSetView(p);const r=check(s);let node=r.scene.nodes.find(x=>x.name===n)||r.scene.nodes.find(x=>x.name===(n==='StartDuelHit'?'StartDuel':n));assert(node,'input target '+n);let x=0,y=0;while(node){const ox=x,oy=y;x=node.matrix.a*ox+node.matrix.c*oy+node.matrix.tx;y=node.matrix.b*ox+node.matrix.d*oy+node.matrix.ty;node=r.scene.nodes.find(x=>x.id===node.parent);}s.playPointer('click',x,y,{observe:false});step(s,1);};
for(let p=1;p<=2;p++){s.playSetView(p);settled();click(p,'StartDuelHit');settled();}
for(let p=1;p<=2;p++)for(const role of (p===1?[1,3,5]:[2,4,6])){s.playSetView(p);settled();click(p,'GridCard'+role);settled();s.playSetView(3-p);settled();}
click(1,'ReadyConfirm');step(s,100);assert(has(s,'ReadyConfirm'));click(2,'ReadyConfirm');
for(let round=1;round<=3;round++){s.playSetView(1);until(s,()=>has(s,'Timer')&&!has(s,'LoadingBar')&&check(s).scene.nodes.find(n=>n.name==='Name1')?.text.startsWith(['刻晴','凯亚','可莉'][round-1]),'round '+round,12000);snap(s,'round-'+round);console.log('NETWORK_ROUND_PASS',round);if(round<3)until(s,()=>has(s,'LoadingBar'),'next round');}
until(s,()=>has(s,'Reselect'),'result');snap(s,'result');click(2,'Reselect');for(let p=1;p<=2;p++){s.playSetView(p);until(s,()=>has(s,'GridCard1')&&!has(s,'LoadingBar'),'return select');assert(!has(s,'Timer'));assert(has(s,'FullscreenBacking'));{const ns=check(s).scene.nodes;const byId=new Map(ns.map(q=>[q.id,q]));const faceGlyphs=ns.filter(x=>/^TextArt\d+$/.test(x.name)&&/^GridFace/.test(byId.get(x.parent)?.name||'')).reduce((a,x)=>a+((x.text||'').match(/\u2588/g)||[]).length,0);assert(faceGlyphs>1000,'select faces repainted after battle: '+faceGlyphs);}}
const logs=check(s).logs.filter(l=>/LOAD METRIC|LOAD PHASE|LOAD SCHEDULE/.test(l.text||''));s.playStop();scenarios.push('GF10 two-player selection, single-ready barrier, three rounds, results and return to selection');
fs.writeFileSync(out+'/flow-verification.json',JSON.stringify({simulatorOnly:true,scenarios,logs,deviceVerified:false,fullscreenDeviceClipVerified:false,powerMeasured:false,richTextVisualVerification:false},null,2));console.log('LOADING_FIX_SCENARIOS_PASS');
