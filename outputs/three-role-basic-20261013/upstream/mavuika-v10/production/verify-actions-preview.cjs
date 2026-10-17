'use strict';const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../dist'),rig=JSON.parse(fs.readFileSync(path.join(root,'assets/neutral-rig-v6.json')));
let draws=0,callback;const ctx=new Proxy({drawImage(im,x,y,w,h,dx,dy,dw,dh){assert(x>=0&&y>=0&&w>0&&h>0);assert(x+w<=im.width&&y+h<=im.height,im.src);assert([dx,dy,dw,dh].every(Number.isFinite));draws++;}}, {get(t,k){return k in t?t[k]:()=>{};},set(t,k,v){t[k]=v;return true;}});
const ids=['compare','group','light','mirror','contact','frame','seek','play','metrics','speed','step'],nodes={};for(const id of ids)nodes[id]={value:'',checked:false,textContent:''};nodes.compare.getContext=()=>ctx;nodes.group.value='idle';nodes.speed.value='5';nodes.contact.value='hit';
class FakeImage{set src(value){this._src=value;const b=fs.readFileSync(path.join(root,value));this.width=b.readUInt32BE(16);this.height=b.readUInt32BE(20);queueMicrotask(()=>this.onload());}get src(){return this._src;}}
const sandbox={document:{getElementById:id=>nodes[id]},Image:FakeImage,fetch:async()=>({ok:true,json:async()=>rig}),requestAnimationFrame:f=>{callback=f;},Light1Model:require('../dist/light1-model.js'),console};vm.createContext(sandbox);vm.runInContext(fs.readFileSync(path.join(root,'neutral-review.js'),'utf8'),sandbox);
(async()=>{await new Promise(resolve=>setImmediate(resolve));assert(callback);let now=0,branches=0;
 for(const group of ['idle','walk','backwalk'])for(const mirror of [false,true])for(const light of [false,true]){
  nodes.group.value=group;nodes.mirror.checked=mirror;nodes.light.checked=light;nodes.group.onchange();for(let i=0;i<12;i++){nodes.seek.value=i%rig.groups[group].poses.length;nodes.seek.oninput();nodes.step.onclick();}branches++;
 }
 for(const contact of ['hit','block','miss','invulnerable','downed','behind'])for(const mirror of [false,true]){
  nodes.group.value='light1';nodes.mirror.checked=mirror;nodes.contact.value=contact;nodes.group.onchange();nodes.play.onclick();for(let i=0;i<60;i++){now+=20;callback(now);}const metric=nodes.metrics.textContent;assert(metric.includes(contact==='hit'?'1 次命中':'0 次命中'),metric);if(contact==='block')assert(metric.includes('1 次防御'),metric);branches++;
 }
 console.log(JSON.stringify({branches,draws,scope:'DOM/canvas substitutes; PNG source bounds and controls checked; not browser/GPU/device QA'}));
})().catch(e=>{console.error(e);process.exitCode=1;});
