'use strict';const assert=require('node:assert/strict'),fs=require('node:fs'),M=require('../dist/light1-model.js'),F=require('../dist/light1-fx-model-v7.js');
const fx=JSON.parse(fs.readFileSync(__dirname+'/../dist/assets/light1-fx-rig-v7.json')),body=JSON.parse(fs.readFileSync(__dirname+'/../dist/assets/neutral-rig-v6.json')).groups.light1,target=JSON.parse(fs.readFileSync(__dirname+'/../dist/assets/v3-target-rig-v7.json')).poses;
const cases=[{name:'hit',target:{x:150},contact:'hit'},{name:'block',target:{x:150,guard:true},contact:'block'},{name:'miss',target:{x:270}},{name:'behind',target:{x:-150}},{name:'invulnerable',target:{x:150,invulnerable:true}},{name:'downed',target:{x:150,downed:true}}];
let branches=0,snapChecks=0,peak=0,visiblePeak=0;const playback={cases:{},scope:'independent paired visual candidate; encoded visible counts exclude buffers/UI/background and do not prove platform performance'};
for(const c of cases)for(const facing of [1,-1])for(const origin of [0,75]){
 const options={x:origin,facing,target:{...c.target,x:origin+c.target.x*facing}},s=M.create(options),frames=[];
 while(!s.ended){
  const before=M.hash(s),effects=F.sample(s);assert.equal(M.hash(s),before,'FX changed simulation');const contacts=effects.filter(e=>e.layer==='contact');
  assert(contacts.length<=1);if(!c.contact)assert.equal(contacts.length,0);else for(const e of contacts){assert(c.contact==='hit'?e.index>=4&&e.index<=7:e.index>=8&&e.index<=11);assert.equal(e.x,s.events[0].contact.x);assert.equal(e.y,s.events[0].contact.y);}
  const restore=M.restore(M.snapshot(s));assert.deepEqual(F.sample(restore),effects);assert.deepEqual(F.receiver(restore),F.receiver(s));snapChecks++;
  const rects=effects.reduce((n,e)=>n+fx.frames[e.index].rectangles,0),receiver=F.receiver(s),targetN=target[receiver.pose].rectangles;peak=Math.max(peak,rects);visiblePeak=Math.max(visiblePeak,rects+body.poses[F.pose(s)].optimizedRectangles+targetN*(receiver.flash>0?2:1));
  frames.push({...M.copy(s),effects,receiver,fxRectangles:rects});M.step(s);
 }
 frames.push({...M.copy(s),effects:F.sample(s),receiver:F.receiver(s),fxRectangles:0});if(c.contact){assert.equal(s.events.length,1);assert.equal(s.events[0].contact.x,origin+132*facing);assert.equal(s.events[0].contact.y,105);}
 assert.deepEqual(F.sample(s),[]);if(facing===1&&origin===0)playback.cases[c.name]=frames;branches++;
}
const right=M.seek({},14),left=M.seek({facing:-1,target:{x:-150}},14);assert.equal(F.landmarks(right).tip.x,-F.landmarks(left).tip.x);assert.equal(F.landmarks(right).tip.y,F.landmarks(left).tip.y);M.interrupt(right);assert.deepEqual(F.sample(right),[]);
const result={branches,snapChecks,fxVisibleEncodedPeak:peak,pairVisibleEncodedPeak:visiblePeak,sourceAlphaZeroFraction:fx.sourceAlphaZeroFraction,contactOnlyFromGeometry:true,fxNeverMutatesSimulation:true,scope:playback.scope};playback.report=result;
fs.writeFileSync(__dirname+'/light1-fx-playback-v7.json',JSON.stringify(playback,null,2)+'\n');fs.writeFileSync(__dirname+'/fx-verification-v7.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
