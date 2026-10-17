import fs from 'node:fs';import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
const out='outputs/nahida-quality-frames-20261015';
const studio=createStudio(JSON.parse(fs.readFileSync(out+'/reimported.simulator.save.json')));
studio.playStart({canvasId:'pc-16-9'});studio.playStep(.01,{observe:false});
const send=(op,v)=>studio.playServerSend('AnimationControl',[op,v]);
const geometry=()=>{const s=studio.playGet({view:true});const nodes=s.scene.nodes.filter(n=>/^S\d{4}$/.test(n.name));assert.equal(nodes.length,994);assert.equal(s.logs.filter(l=>['error','lua-error'].includes(l.level)).length,0);return JSON.stringify(nodes);};
const checks=[];
for(const action of ['idle','move']){
 send('action',action);
 for(let frame=1;frame<=4;frame++){
  send('frame',frame);const expected=geometry();send('frame',frame%4+1);const next=geometry();assert.notEqual(expected,next);
  send('frame',frame);send('pause',0);studio.playStep(.10,{observe:false});assert.equal(geometry(),expected,'Geometry changed inside frame');
  studio.playStep(.081,{observe:false});assert.equal(geometry(),next,'Frame boundary did not use complete next pose');
  checks.push({action,frame,geometryHeldWithinFrame:true,nextFrameExact:true});
 }
}
fs.writeFileSync(out+'/frame-animation-verification.json',JSON.stringify({frameDurationMs:180,interpolation:false,imagePoolSize:994,checks,deviceVerified:false},null,2));
console.log('8 frames: held geometry and exact frame-boundary replacement passed');
