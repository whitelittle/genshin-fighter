import {readFileSync,writeFileSync} from 'node:fs';import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {renderPaintPng} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';
const save=JSON.parse(readFileSync('outputs/demo-solo-light/fighter.save.json'));save.assets.scripts[0].source+='\nlocal start=OnStart\nfunction OnStart()start();aiEnabled=false;draw()end';
const results=[];
for(const canvasId of ['mobile-16-9','mobile-19.5-9','mobile-4-3']){
 const s=createStudio(save);s.playStart({canvasId});let r=s.playGet({view:true});assert.equal(r.logs.filter(l=>['error','lua-error'].includes(l.level)).length,0);
 for(const name of ['Stick1','Stick9','Light','Heavy','Block','Jump','RoleKeqing','SelectStage3']){const n=r.scene.nodes.find(n=>n.name===name);assert.ok(Math.abs(n.matrix.tx)+n.sourceWidth/2<=r.canvasWidth/2,name+' off canvas');assert.ok(Math.abs(n.matrix.ty)+n.sourceHeight/2<=r.canvasHeight/2,name+' off canvas');}
 const n=r.scene.nodes.find(n=>n.name==='Stick5'),x=n.matrix.tx+r.canvasWidth/2,y=n.matrix.ty+r.canvasHeight/2;
 for(const [type,xx,yy]of[['down',x,y],['move',x,y-48],['move',x+48,y-48],['move',x+48,y]])s.playPointer(type,xx,yy,{observe:false});s.playClick('Light',{observe:false});s.playPointer('up',x+280,y,{observe:false});s.playStep(1/30,{observe:false});r=s.playGet({view:true,paint:true});assert.ok(r.scene.nodes.find(n=>n.name==='Stats').text.includes('雷霆突进斩'));
 writeFileSync('outputs/demo-solo-light/'+canvasId+'.png',renderPaintPng(r.paint,r.canvasWidth,r.canvasHeight).data);results.push({canvasId,size:[r.canvasWidth,r.canvasHeight],controlBounds:true,touch236:true});
}
writeFileSync('assets/demo/mobile-verification.json',JSON.stringify({simulatorVerified:true,deviceVerified:false,multitouchDeviceVerified:false,results},null,2));console.log(JSON.stringify(results));
