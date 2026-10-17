import fs from 'node:fs';import assert from 'node:assert/strict';import crypto from 'node:crypto';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {renderPaintPng} from '../outputs/nahida-independent-actions-20261015/transparent-native-renderer.mjs';
const out='outputs/nahida-independent-actions-20261015';
const studio=createStudio(JSON.parse(fs.readFileSync(out+'/reimported.simulator.save.json')));
studio.playStart({canvasId:'pc-16-9'});studio.playStep(.01,{observe:false});
const send=(op,v)=>studio.playServerSend('AnimationControl',[op,v]);
const image=()=>{const s=studio.playGet({view:true,paint:true});assert.equal(s.logs.filter(l=>['error','lua-error'].includes(l.level)).length,0);assert.equal(s.scene.nodes.filter(n=>/^S\d{4}$/.test(n.name)).length,994);return renderPaintPng(s.paint,s.canvasWidth,s.canvasHeight).data;};
const hash=()=>crypto.createHash('sha256').update(image()).digest('hex');
const results=[];
for(const action of ['idle','move']){
 send('action',action);
 for(let f=1;f<=4;f++){send('frame',f);const initial=hash();send('action',action==='idle'?'move':'idle');send('frame',4);send('action',action);send('frame',f);assert.equal(hash(),initial,'Old pose leaked after switching actions');fs.writeFileSync(`${out}/${action}/${f-1}/native.png`,image());results.push({action,frame:f,roundTripIdentical:true,images:994});}
}
send('action','move');send('frame',1);const before=hash();
send('pause',0);studio.playStep(.35,{observe:false});const middle=hash();assert.notEqual(middle,before);
fs.writeFileSync(out+'/native-transition.png',image());
studio.playStep(.15,{observe:false});send('pause',1);const settled=hash();send('frame',2);assert.equal(hash(),settled,'Transition endpoint differs from fitted keyframe');
fs.writeFileSync(out+'/native-preview.png',image());
fs.writeFileSync(out+'/transform-verification.json',JSON.stringify({frames:results,intermediateGeometryChanged:true,transitionEndpointExact:true,oldPoseDoesNotAccumulate:true,imagePoolSize:994,twoPoseAlphaCrossfade:false,deviceVerified:false,artApproved:false},null,2));
console.log('8 pose round trips and geometric transition endpoint passed');
