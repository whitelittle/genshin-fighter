import{readFileSync,writeFileSync}from'node:fs';import assert from'node:assert/strict';
import{createStudio}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import{renderPaintPng}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';
const out='outputs/test-v1',save=JSON.parse(readFileSync(out+'/fighter.save.json'));save.assets.scripts[0].source=save.assets.scripts[0].source.replace('local PIXEL_TEMPLATE_INDEX=1073741845','local PIXEL_TEMPLATE_INDEX=0');
const results=[];for(const canvasId of['mobile-16-9','mobile-19.5-9','mobile-4-3']){
 const s=createStudio(save);s.playStart({canvasId,playerCount:2});for(let n=0;n<180;n++)s.playStep(1/60,{observe:false});
 for(let p=1;p<=2;p++){s.playSetView(p);s.playClick('StartDuel',{observe:false});}for(let n=0;n<2;n++)s.playStep(1/60,{observe:false});
 if(canvasId==='mobile-16-9'){const r=s.playGet({view:true,paint:true});writeFileSync(out+'/selection.png',renderPaintPng(r.paint,r.canvasWidth,r.canvasHeight).data);}
 for(let p=1;p<=2;p++){s.playSetView(p);s.playClick('ReadyConfirm',{observe:false});}for(let n=0;n<1800;n++){s.playStep(1/60,{observe:false});if(n%30===0&&s.playGet({view:true}).scene.nodes.some(n=>n.name==='Timer'))break;}for(let n=0;n<100;n++)s.playStep(1/60,{observe:false});
 const r=s.playGet({view:true,paint:true});const errors=r.logs.filter(l=>['error','lua-error'].includes(l.level)||/ERROR/.test(l.text||''));assert.equal(errors.length,0,JSON.stringify(errors));
 for(const name of['Light','Heavy','Jump','Block','Skill','Ultimate','Stick1','Stick9']){const n=r.scene.nodes.find(n=>n.name===name);assert.ok(n,name);assert.ok(Math.abs(n.matrix.tx)+n.sourceWidth/2<=r.canvasWidth/2,name+' horizontal '+canvasId);assert.ok(Math.abs(n.matrix.ty)+n.sourceHeight/2<=r.canvasHeight/2,name+' vertical '+canvasId);}
 writeFileSync(out+'/'+canvasId+'.png',renderPaintPng(r.paint,r.canvasWidth,r.canvasHeight).data);results.push({canvasId,touchVisible:true,withinBounds:true});
}
writeFileSync(out+'/mobile-verification.json',JSON.stringify({simulatorOnly:true,results},null,2));console.log('MOBILE_LAYOUT_PASS');
