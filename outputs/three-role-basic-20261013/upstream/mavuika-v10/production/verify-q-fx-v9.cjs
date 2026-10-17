const assert=require('node:assert/strict'),fs=require('node:fs'),Q=require('../dist/q-model.js'),FX=require('../dist/q-fx-model-v9.js');
const previous=FX.frame(Q.seek('hit',73)),landed=FX.frame(Q.seek('hit',74));assert(Math.abs(previous.receiver.x-landed.receiver.x)<1);assert(Math.abs(previous.receiver.y-landed.receiver.y)<1);
const playback={};let snapshots=0;for(const action of ['q','heavy','dash'])for(const outcome of ['hit','block','miss','invulnerable','downed','range']){
const s=Q.create(outcome,action),seq=[];while(!s.ended){Q.step(s);const before=Q.snapshot(s),f=FX.frame(s);assert.deepEqual(s,before);assert.deepEqual(f,FX.frame(Q.snapshot(s)));assert(f.layers.every(x=>x.alpha>=0&&x.alpha<=1&&Number.isFinite(x.x)&&Number.isFinite(x.y)));
if(action==='q'&&outcome!=='hit')assert(!f.layers.some(l=>['sun-open','sun-full','sun-fade','charge','blade-prepare','slash','slash-residue','impact'].includes(l.id)));
if(outcome!=='hit')assert(!f.layers.some(l=>['impact','impact-fade'].includes(l.id)));
if(action!=='q'&&s.tick>=12)assert.equal(f.body.pose,'brake');if(s.action==='q'&&s.confirmed&&s.tick>=74){assert.equal(f.body.y,s.origin.y);assert(!['ride','brake'].includes(f.body.pose));}
assert(f.layers.every(x=>['rear','ground','front'].includes(x.plane)));for(const l of f.layers){if(l.id.startsWith('sun')||['wheel-trail','slash','slash-residue'].includes(l.id))assert.equal(l.plane,'rear');if(['brake-sparks','skid-residue'].includes(l.id))assert.equal(l.plane,'ground');if(l.id.startsWith('impact')||l.bank==='light')assert.equal(l.plane,'front');}if(s.ended)assert.equal(f.layers.length,0);
seq.push({state:Q.snapshot(s),frame:f});snapshots++;
}playback[action+'-'+outcome]=seq;
assert.equal(s.hits,outcome==='hit'?1:0);if(outcome==='block')assert(seq.some(x=>x.frame.layers.some(l=>l.bank==='light')));
}
for(const action of ['q','heavy','dash'])for(let tick=0;tick<(action==='q'?99:54);tick++){
const s=Q.seek('hit',tick,action),other=Q.seek('hit',tick,action,{x:530,y:480}),a=FX.frame(s),b=FX.frame(other);
for(let i=0;i<a.layers.length;i++){const fixed=a.layers[i].id.startsWith('sun');assert(Math.abs(b.layers[i].x-a.layers[i].x-(fixed?0:100))<1e-8);assert(Math.abs(b.layers[i].y-a.layers[i].y-(fixed?0:30))<1e-8);}
}
fs.writeFileSync('production/q-fx-playback-v9.json',JSON.stringify(playback));console.log(JSON.stringify({branches:18,snapshots,damageEvents:'one on selected hit; zero otherwise',fxMutation:false,scope:'preview-selected contact; CPU presentation tests'}));
