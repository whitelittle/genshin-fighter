import{readFileSync,writeFileSync}from'node:fs';import assert from'node:assert/strict';
import{createStudio}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import{renderPaintPng}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';
const out='outputs/roster-v2',save=JSON.parse(readFileSync(out+'/fighter.save.json'));save.assets.scripts[0].source=save.assets.scripts[0].source.replace('local PIXEL_TEMPLATE_INDEX=1073741845','local PIXEL_TEMPLATE_INDEX=0');const results=[];
for(const canvasId of['mobile-19.5-9','mobile-4-3']){
 const s=createStudio(save);s.playStart({canvasId,playerCount:2});const check=()=>{const r=s.playGet({view:true});assert.ok(!r.logs.some(l=>l.level==='lua-error'||/ERROR|加载失败/.test(l.text||'')),JSON.stringify(r.logs.slice(-4)));return r;};
 const step=n=>{for(let i=0;i<n;i++)s.playStep(1/60,{observe:false});return check();};
 for(let n=0;n<10000;n+=30){if(check().scene.nodes.some(n=>n.name==='StartDuel'))break;step(30);}
 s.playSetView(1);s.playClick('StartDuel',{observe:false});step(1);const r=s.playGet({view:true,paint:true});
 for(const name of['ReadyConfirm','TeamSlot11','TeamSlot23','PagePrev','PageNext']){const n=r.scene.nodes.find(n=>n.name===name);assert.ok(n,name);assert.ok(Math.abs(n.matrix.tx)+n.sourceWidth*Math.abs(n.matrix.a)/2<=r.canvasWidth/2+1,name+' outside horizontal '+canvasId);assert.ok(Math.abs(n.matrix.ty)+n.sourceHeight*Math.abs(n.matrix.d)/2<=r.canvasHeight/2+1,name+' outside vertical '+canvasId);}
 writeFileSync(out+'/'+canvasId+'-select.png',renderPaintPng(r.paint,r.canvasWidth,r.canvasHeight).data);results.push({canvasId,selectionWithinBounds:true});console.log('MOBILE_SELECT_PASS',canvasId);s.playStop();
}
writeFileSync(out+'/mobile-verification.json',JSON.stringify({simulatorOnly:true,results,deviceVerified:false},null,2));
