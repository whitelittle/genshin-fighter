const assert=require('node:assert/strict'),Q=require('../dist/q-model.js');
const outcomes=['hit','block','miss','invulnerable','downed','range'];let resumeChecks=0;
for(const action of ['q','heavy','dash'])for(const outcome of outcomes){
 const origin={x:380,y:470},s=Q.create(outcome,action,origin);let guard=0;
 while(!s.ended&&guard++<200)Q.step(s);
 assert(s.ended);assert.equal(s.hits,outcome==='hit'?1:0);
 assert.deepEqual(s.events.map(e=>e.tick),outcome==='hit'?[action==='q'?55:20]:[]);
 assert.equal(s.tick,action==='q'?(outcome==='hit'?104:28):54);
 if(action==='q')assert.deepEqual(Q.choreography(s),{...origin,pose:'idle'});
 for(let wall=0;wall<=135;wall++){
  const a=Q.create(outcome,action,origin);for(let i=0;i<wall;i++)Q.step(a);
  const b=Q.snapshot(a);for(let i=wall;i<200;i++){Q.step(a);Q.step(b);}assert.deepEqual(a,b);resumeChecks++;
 }
 const before=Q.snapshot(s);for(let i=0;i<10;i++)Q.step(s);assert.deepEqual(s,before);
 if(action==='q'&&outcome!=='hit'){
  for(let t=8;t<=104;t++){const p=Q.seek(outcome,t);assert(p.failed);assert.equal(p.events.length,0);assert(!['windup','slash'].includes(Q.choreography(p).pose));assert.equal(Q.choreography(p).y,450);}
 }
}
const gate=Q.seek('hit',8);assert(gate.confirmed);assert.equal(gate.hits,0);assert.equal(gate.events.length,0);
const impact=Q.seek('hit',55),location=Q.choreography(impact);
for(let i=0;i<12;i++){Q.step(impact);assert.equal(impact.tick,55);assert.deepEqual(Q.choreography(impact),location);}Q.step(impact);assert.equal(impact.tick,56);assert.equal(impact.hits,1);
for(let tick=0;tick<=104;tick++){
 const s=Q.seek('hit',tick);assert.equal(s.tick,tick);assert.equal(s.hits,tick>=55?1:0);
 const c=Q.choreography(s);assert.equal(c.pose,tick<9?'idle':tick<32?'ride':tick<55?'windup':tick<86?'slash':'idle');
 assert(Number.isFinite(c.x)&&Number.isFinite(c.y));
}
assert.deepEqual(Q.choreography(Q.seek('hit',0)),{x:430,y:450,pose:'idle'});
assert.deepEqual(Q.choreography(Q.seek('hit',31)),{x:650,y:230,pose:'ride'});
for(const origin of [{x:430,y:450},{x:175,y:470}])for(let tick=74;tick<=104;tick++)assert.deepEqual(Q.choreography(Q.seek('hit',tick,'q',origin)),{...origin,pose:tick<86?'slash':'idle'});
for(const [dx,dy,confirmed] of [[80,0,true],[120,40,true],[121,0,false],[80,41,false],[-1,0,false],[600,0,false]]){const origin={x:430,y:450},s=Q.create('hit','q',origin,{x:430+dx,y:450+dy});while(!s.ended)Q.step(s);assert.equal(s.confirmed,confirmed);assert.equal(s.hits,confirmed?1:0);assert.equal(s.tick,confirmed?104:28);}
assert.throws(()=>Q.seek('hit',NaN));assert.throws(()=>Q.create('bad'));
console.log(JSON.stringify({branches:18,resumeChecks,damageTick:55,confirmationTick:8,hitstop:12,failedEndTick:28,scope:'isolated preview model; formal combat untested'}));
