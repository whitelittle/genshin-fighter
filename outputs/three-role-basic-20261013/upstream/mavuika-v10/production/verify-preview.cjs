/* Executes renderer paths with a fake canvas; not a real browser visual test. */
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const els=new Map();const ids=['stage','phase','readout','scrub','hitCount','subtitle','play','restart','step','speed','sound','outcome','mirror','reduced','middle','status','action','material'];for(let i=1;i<=3;i++)for(const k of ['label','title','text'])ids.push(`beat${i}-${k}`);
let draws=0;const spriteDraws=[];const ctx=new Proxy({},{get:(_,key)=>(...args)=>{draws++;if(key==='drawImage')spriteDraws.push(args);},set:()=>true});
for(const id of ids)els.set(id,{value:id==='material'?'source':id==='outcome'?'hit':id==='action'?'q':id==='speed'?'1':'0',checked:false,disabled:true,getContext:()=>ctx});
class Img{set src(value){this.path=value;queueMicrotask(()=>this.onload());}}
const sandbox={document:{getElementById:id=>{assert(els.has(id),id);return els.get(id);}},Image:Img,fetch:async()=>({ok:true,json:async()=>JSON.parse(fs.readFileSync('dist/assets/rig.json'))}),performance:{now:()=>0},requestAnimationFrame:()=>{},console,window:{},queueMicrotask};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync('dist/q-model.js','utf8'),sandbox);vm.runInContext(fs.readFileSync('dist/app.js','utf8'),sandbox);
(async()=>{await new Promise(r=>setImmediate(r));assert.equal(els.get('play').disabled,false);
 for(const material of ['source','initial','optimized'])for(const action of ['q','heavy','dash'])for(const outcome of ['hit','block','miss','invulnerable','downed','range'])for(const reduced of [true,false])for(const mirror of [true,false]){
  els.get('material').value=material;els.get('action').value=action;els.get('outcome').value=outcome;els.get('reduced').checked=reduced;els.get('mirror').checked=mirror;
  vm.runInContext('reset();',sandbox);for(let t=0;t<135;t++)vm.runInContext('advance();draw();',sandbox);
  assert.equal(els.get('hitCount').textContent,`${outcome==='hit'?1:0} 次命中`);
 }
 els.get('middle').onclick();const lastSprite=spriteDraws.at(-1);const rig=JSON.parse(fs.readFileSync('dist/assets/rig.json'));assert.deepEqual(lastSprite.slice(1,5),rig.materials.optimized.poses.slash.rect);assert.equal(els.get('subtitle').textContent,'「太阳的轰鸣！」');assert.equal(els.get('action').value,'q');
 console.log(JSON.stringify({status:'passed',branches:216,renderSteps:29160,canvasCalls:draws,scope:'fake-canvas renderer control flow only; no actual browser/device QA'}));
})().catch(e=>{console.error(e);process.exitCode=1;});
