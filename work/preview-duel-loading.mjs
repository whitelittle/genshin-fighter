import {readFileSync,writeFileSync}from'node:fs';import assert from'node:assert/strict';
import {createStudio}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {renderPaintPng}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';
const out='outputs/duel-loading',s=createStudio(JSON.parse(readFileSync(out+'/fighter.save.json')));
s.playStart({playerCount:1});
function shot(name){const r=s.playGet({view:true,paint:true});writeFileSync(out+'/'+name+'.png',renderPaintPng(r.paint,r.canvasWidth,r.canvasHeight).data);const errors=r.logs.filter(l=>['error','lua-error'].includes(l.level)||/ERROR:/.test(l.text||''));assert.equal(errors.length,0,JSON.stringify(errors));return r;}
let r=shot('01-loading-start');let done=false,half=false,updates=0;
for(;updates<1800;updates++){
 s.playStep(1/60,{observe:false});
 if(updates%30!==0)continue;
 r=s.playGet({view:true});const label=r.scene.nodes.find(n=>n.name==='LoadingText');
 if(label?.text.includes('失败'))throw Error(label.text);
 if(!half&&/加载 (?:[4-7]\d)%/.test(label?.text||'')){shot('02-loading-progress');half=true;}
 const home=r.scene.nodes.find(n=>n.name==='StartDuel');
 if(home&&!r.scene.nodes.some(n=>n.name==='LoadingText')){done=true;break;}
}
assert.ok(done,'loading never completed');r=shot('03-home');
const diag=r.scene.nodes.find(n=>n.name==='BootDiagnostic');assert.ok(!diag?.text.includes('ERROR:'),diag?.text);
s.playClick('StartDuel',{observe:false});s.playStep(1/60,{observe:false});shot('04-select');
writeFileSync(out+'/preview.json',JSON.stringify({loadingCompleted:done,updates,errors:[],simulatorOnly:true},null,2));console.log({updates,done,half});
