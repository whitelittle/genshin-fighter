import{readFileSync,writeFileSync,existsSync}from'node:fs';import vm from'node:vm';import assert from'node:assert/strict';
const s={window:{},Math};vm.createContext(s);vm.runInContext(readFileSync('outputs/motion-production/model.js','utf8'),s);const M=s.window.MotionProductionModel;
for(const key of['klee','yanfei']){
 const root=`outputs/motion-group1/${key}`,r=JSON.parse(readFileSync(root+'/manifest.json','utf8')).roles[0],ids=new Set(r.frames.map(f=>f.id));assert.equal(ids.size,48);let samples=0;
 for(const f of r.frames){assert(existsSync(root+'/'+f.png));assert(!f.edgeRisk);assert(f.pixelAnchor.every(Number.isFinite));}
 for(const a of M.flow)for(let i=0;i<M.duration(r,a);i++){assert(ids.has(M.pose(r,a,i)));samples++;}
 for(const outcome of['hit','guard','whiff']){assert.equal(M.sample(r,'Q',r.design.moves.Q.startup+61,outcome,100).damage,outcome==='hit'?r.design.moves.Q.damage:0);}
 const report={passed:true,frames:48,poseSamples:samples,actions:M.flow.length,pool:r.pool,artStatus:'candidate',projectiles:'detached source bombs excluded from actor; separate visuals pending',productionCombatChanged:false,deviceVerified:false};writeFileSync(root+'/verification.json',JSON.stringify(report,null,2));console.log(key,report);
}
