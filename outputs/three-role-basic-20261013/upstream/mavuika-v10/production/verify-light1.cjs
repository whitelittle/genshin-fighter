'use strict';const assert=require('node:assert/strict'),M=require('../dist/light1-model.js');
const cases=[{name:'hit',target:{x:150},hits:1},{name:'block',target:{x:150,guard:true},hits:0,blocked:1},{name:'miss',target:{x:270},hits:0},{name:'behind',target:{x:-150},hits:0},{name:'invulnerable',target:{x:150,invulnerable:true},hits:0},{name:'downed',target:{x:150,downed:true},hits:0},{name:'touch-far-edge',target:{x:244,width:36},hits:0},{name:'inside-far-edge',target:{x:243,width:36},hits:1},{name:'high',target:{x:150,y:130},hits:0},{name:'low',target:{x:150,height:70},hits:0}];
let resumed=0,branches=0;
for(const c of cases)for(const facing of [1,-1])for(const origin of [0,75]){
 const options={facing,x:origin,target:{...c.target,x:origin+c.target.x*facing}},s=M.create(options),snaps=[];
 while(!s.ended){snaps.push(M.snapshot(s));M.step(s);assert(s.events.length<=1);assert(s.hits<=1);}
 assert.equal(s.hits,c.hits,c.name);assert.equal(s.blocked,c.blocked||0,c.name);assert.equal(s.tick,36);
 if(c.hits)assert.deepEqual(s.events.map(e=>[e.tick,e.damage,e.knockback]),[[14,32,facing*20]]);
 assert.equal(s.wallTick,36+(c.hits?6:c.blocked?3:0));
 for(const snap of snaps){const r=M.restore(snap);while(!r.ended)M.step(r);assert.equal(M.hash(r),M.hash(s));resumed++;}
 for(const snap of snaps.filter(s=>s.stop>0)){const r=M.copy(snap),before=r.tick;M.step(r);assert.equal(r.tick,before);}
 branches++;
}
const interrupted=M.create();for(let i=0;i<9;i++)M.step(interrupted);M.interrupt(interrupted);for(let i=0;i<40;i++)M.step(interrupted);assert.equal(interrupted.hits,0);
console.log(JSON.stringify({branches,resumed,active:[14,16],singleHitAt:14,hitstop:6,checks:'geometry, mirror, translated origin, edge boundary, block, immunity, downed, interrupt, snapshot/hash resumes',scope:'independent candidate; no formal combat/device acceptance'}));
