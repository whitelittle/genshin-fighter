import{readFileSync as read,writeFileSync as write}from'node:fs';import assert from'node:assert/strict';
import{createStudio}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
const out=process.env.REPAIR_OUT||'outputs/test-repair-v1',save=JSON.parse(read(out+'/simulator.save.json'));
save.assets.scripts[0].source+=`
resourceGate.inspect=function()
 local retained,working=0,0;for _,frames in ipairs(spriteData)do for _,fr in ipairs(frames)do if fr.rows or fr.decoder then retained=retained+1 end;if fr.decoder then working=working+1 end end end
 print('[PREFETCH CHECK] '..tostring(resourceGate.loader.prefetchKey)..' cached='..retained..' working='..working)
end
local loaderTestUpdate=OnUpdate
function OnUpdate(dt)loaderTestUpdate(dt);if not resourceGate.busy and resourceGate.loader.lastProbe~=resourceGate.loader.prefetchKey then resourceGate.loader.lastProbe=resourceGate.loader.prefetchKey;resourceGate.inspect()end end`;
const s=createStudio(save);s.playStart({playerCount:2,canvasId:'mobile-19.5-9'});
const check=()=>{const r=s.playGet({view:true});assert(!r.logs.some(l=>['error','lua-error'].includes(l.level)||/ERROR|加载失败/.test(l.text||'')),JSON.stringify(r.logs.slice(-6)));return r;};
const step=n=>{for(let k=0;k<n;k++)s.playStep(1/60,{observe:false});return check();};
const until=(f,label)=>{for(let i=0;i<16000;i+=30){if(f())return;step(30);}throw Error('timeout '+label);};
const has=n=>check().scene.nodes.some(x=>x.name===n),settled=()=>until(()=>!has('LoadingText'),'settle');
const click=n=>{s.playClick(n,{observe:false});step(1);};
let first=check(),black=first.scene.nodes.find(n=>n.name==='LoadingBlack');assert(black);assert.equal(black.sourceWidth,first.canvasWidth);assert.equal(black.sourceHeight,first.canvasHeight);
settled();click('StartDuelHit');assert(has('LoadingBlack'),'home to select must be black');settled();
for(const n of[3,8,5]){click('GridCard'+n);settled();}
click('ReadyConfirm');step(120);assert(has('ReadyConfirm'),'one locked team must remain selection');
assert(check().logs.some(l=>/PREFETCH CHECK.*3:0/.test(l.text||'')),'locked first fighter not queued');
click('ReadyConfirm');step(2);const canceled=check().logs.filter(l=>/PREFETCH CHECK.*0:0/.test(l.text||'')).at(-1);assert(canceled&&/cached=0 working=0/.test(canceled.text),'cancel must release stale prefetched fighters');
// Same-page preview shrink must reuse a previously allocated pool.
click('GridCard5');settled();const metric=check().logs.filter(l=>/LOAD METRIC/.test(l.text||'')).at(-1);assert(metric&&/destroy=0/.test(metric.text),'same-page avatar shrink unexpectedly destroyed controls');
write(out+'/loading-verification.json',JSON.stringify({simulatorOnly:true,canvas:'mobile-19.5-9',fullscreenLoading:true,homeToSelectionBlack:true,oneLockedTeamCannotStart:true,canceledPrefetchReleased:true,previewPoolReuse:true,metrics:check().logs.filter(l=>/LOAD METRIC|PREFETCH CHECK/.test(l.text||'')),deviceVerified:false},null,2));console.log('LOADER_CANCEL_REUSE_FULLSCREEN_PASS');
