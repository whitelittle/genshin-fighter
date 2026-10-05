import {readFileSync,writeFileSync} from 'node:fs';import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {renderPaintPng} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';
const out='outputs/duel-vnext',save=JSON.parse(readFileSync(out+'/fighter.save.json'));
const s=createStudio(save);s.playStart({playerCount:2});
const shot=name=>{const r=s.playGet({view:true,paint:true});writeFileSync(out+'/'+name+'.png',renderPaintPng(r.paint,r.canvasWidth,r.canvasHeight).data);return r;};
const errors=r=>[...r.logs.filter(l=>['error','lua-error'].includes(l.level)||/ERROR:/.test(l.text||'')),...r.scene.nodes.filter(n=>n.name==='BootDiagnostic'&& /(?:INIT|START|UPDATE) ERROR/.test(n.text||''))];
let r=shot('01-start');console.log('start',JSON.stringify(errors(r)));assert.equal(errors(r).length,0);
for(let p=1;p<=2;p++){s.playSetView(p);s.playClick('StartDuel',{observe:false});}
for(let n=0;n<4;n++)s.playStep(1/60,{observe:false});r=shot('02-select');console.log('select',JSON.stringify(errors(r)));assert.equal(errors(r).length,0);
s.playSetView(1);s.playClick('ChooseKeqing',{observe:false});s.playClick('ReadyConfirm',{observe:false});
for(let n=0;n<75;n++)s.playStep(1/60,{observe:false});
r=s.playGet({view:true});assert.ok(!r.scene.nodes.some(n=>n.name==='RoundBanner'&&n.visible!==false),'one ready must not start');assert.ok(r.scene.nodes.some(n=>n.name==='ReadyConfirm'),'selection stays visible');
s.playSetView(2);s.playClick('ChooseDiluc',{observe:false});s.playClick('ReadyConfirm',{observe:false});
for(let n=0;n<65;n++)s.playStep(1/60,{observe:false});r=shot('03-round-intro');console.log('intro',JSON.stringify(errors(r)));assert.equal(errors(r).length,0);
for(let n=0;n<95;n++)s.playStep(1/60,{observe:false});r=shot('04-fight');console.log('fight',JSON.stringify(errors(r)));assert.equal(errors(r).length,0);
assert.ok(r.scene.nodes.some(n=>n.name==='Light'),'both-ready must start');
console.log(r.scene.nodes.filter(n=>['Status','BootDiagnostic','Stats'].includes(n.name)).map(n=>({name:n.name,text:n.text})));
for(const [p,name,frames]of [[1,'Light',35],[2,'Skill',25],[2,'Skill',24],[2,'Skill',75],[1,'Skill',38],[1,'Skill',50],[1,'Jump',20]]){s.playSetView(p);s.playClick(name,{observe:false});for(let n=0;n<frames;n++)s.playStep(1/60,{observe:false});r=s.playGet({view:true});assert.equal(errors(r).length,0,JSON.stringify(errors(r)));}
shot('05-action');
for(let n=0;n<110;n++)s.playStep(1/60,{observe:false});
const a=s.playSetView(1,{view:true}),b=s.playSetView(2,{view:true});
for(const name of ['Hp1','Hp2','Timer','Keqing','Diluc'])assert.deepEqual(a.scene.nodes.find(n=>n.name===name),b.scene.nodes.find(n=>n.name===name),name+' diverged');
const mobile=[];
for(const canvasId of ['mobile-16-9','mobile-19.5-9','mobile-4-3']){
 const m=createStudio(save);m.playStart({canvasId,playerCount:2});for(let p=1;p<=2;p++){m.playSetView(p);m.playClick('StartDuel',{observe:false});m.playClick('ReadyConfirm',{observe:false});}
 for(let n=0;n<180;n++)m.playStep(1/60,{observe:false});const v=m.playGet({view:true,paint:true});assert.equal(errors(v).length,0);
 for(const name of ['Light','Heavy','Block','Jump','Skill','Ultimate','Stick1','Stick9']){const n=v.scene.nodes.find(n=>n.name===name);assert.ok(n,name);assert.ok(Math.abs(n.matrix.tx)+n.sourceWidth/2<=v.canvasWidth/2,name+' horizontal overflow '+canvasId);assert.ok(Math.abs(n.matrix.ty)+n.sourceHeight/2<=v.canvasHeight/2,name+' vertical overflow '+canvasId);}
 writeFileSync(out+'/'+canvasId+'.png',renderPaintPng(v.paint,v.canvasWidth,v.canvasHeight).data);mobile.push({canvasId,controlBounds:true});
}
writeFileSync(out+'/verification.json',JSON.stringify({simulatorVerified:true,deviceVerified:false,oneReadyDoesNotStart:true,menuToFight:true,actionSmoke:true,twoRuntimeViewMatch:true,mobile},null,2));
