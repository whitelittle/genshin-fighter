import fs from 'node:fs';import assert from 'node:assert/strict';import crypto from 'node:crypto';
import{createStudio}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
const out=process.env.REPAIR_OUT||'outputs/midphase-final';
const save=JSON.parse(fs.readFileSync(out+'/simulator.save.json'));
const s=createStudio(save);s.playStart({playerCount:2});
function get(){const r=s.playGet({view:true});assert(!r.logs.some(l=>['error','lua-error'].includes(l.level)||/START ERROR|INIT ERROR|RESOURCE ERROR/.test(l.text||'')),JSON.stringify(r.logs.slice(-6)));return r;}
function step(n){for(let i=0;i<n;i++)s.playStep(1/60,{observe:false});}
function has(name){return get().scene.nodes.some(n=>n.name===name);}
function settle(){for(let i=0;i<15000;i+=30){if(!has('LoadingText'))return;step(30);}throw Error('Loading timeout');}
function click(player,name){s.playSetView(player);const r=get();let node=r.scene.nodes.find(n=>n.name===(name==='StartDuelHit'?'StartDuel':name));assert(node,name);let x=0,y=0;while(node){const oldX=x,oldY=y;x=node.matrix.a*oldX+node.matrix.c*oldY+node.matrix.tx;y=node.matrix.b*oldX+node.matrix.d*oldY+node.matrix.ty;node=r.scene.nodes.find(n=>n.id===node.parent);}s.playPointer('click',x,y,{observe:false});step(1);}
settle();for(let p=1;p<=2;p++){click(p,'StartDuelHit');settle();}
const checks=[];
for(let p=1;p<=2;p++){
 for(let n of [p,3,5]){click(p,'GridCard'+n);settle();s.playSetView(3-p);settle();}
 s.playSetView(p);const hint=get().scene.nodes.find(n=>n.name==='SelectionHint')?.text;assert(hint?.includes('3/3'),hint);checks.push('P'+p+' real pointer three selections');
}
for(let p=1;p<=2;p++)click(p,'ReadyConfirm');
for(let i=0;i<22000;i+=30){if(has('Timer')&&!has('LoadingText'))break;step(30);}
assert(has('Timer')&&!has('LoadingText'),'both ready starts battle');checks.push('Two-player ready/load/start');
s.playStop();fs.writeFileSync(out+'/selection-input-verification.json',JSON.stringify({checks,sourceSha256:crypto.createHash('sha256').update(save.assets.scripts[0].source).digest('hex'),pixelTemplateIndex:1073742822,simulatorVerified:true,officialVerified:false},null,2));console.log(JSON.stringify(checks));
