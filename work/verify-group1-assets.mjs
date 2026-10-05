import{readFileSync,writeFileSync,existsSync}from'node:fs';import vm from'node:vm';import assert from'node:assert/strict';
const ctx={window:{},Math};vm.createContext(ctx);vm.runInContext(readFileSync('outputs/motion-production/model.js','utf8'),ctx);const M=ctx.window.MotionProductionModel;
const batch=JSON.parse(readFileSync('outputs/motion-production/batch-plan.json','utf8')).batches[0].roles,reports=[];
for(const[key]of batch){
 const root='outputs/motion-group1/'+(key==='klee'?'klee-approved-v3':key);if(!existsSync(root+'/manifest.json')){reports.push({key,pending:true});continue;}
 const r=JSON.parse(readFileSync(root+'/manifest.json','utf8')).roles[0];
 if(existsSync(root+'/弃用标记.json')){const rejected=JSON.parse(readFileSync(root+'/弃用标记.json','utf8')).files||[];if(r.frames.some(f=>rejected.includes(f.source))){reports.push({key,pending:true,rejectedSource:true});continue;}}
 const ids=new Set(r.frames.map(f=>f.id));assert.equal(ids.size,48);let samples=0;
 for(const f of r.frames){assert(existsSync(root+'/'+f.png));assert(!f.edgeRisk);assert(f.pixelAnchor.every(Number.isFinite));}
 for(const action of M.flow)for(let i=0;i<M.duration(r,action);i++){assert(ids.has(M.pose(r,action,i)),key+' '+action+' '+i);samples++;}
 for(const outcome of['hit','guard','whiff'])assert.equal(M.sample(r,'Q',r.design.moves.Q.startup+61,outcome,100).damage,outcome==='hit'?r.design.moves.Q.damage:0);
 const row={key,passed:true,stateSlots:48,uniqueSourceFrames:r.uniqueSourceFrames||48,poseSamples:samples,actions:M.flow.length,pool:r.pool,artStatus:'candidate',modelOnly:true,deviceVerified:false};reports.push(row);writeFileSync(root+'/verification.json',JSON.stringify(row,null,2));
}
writeFileSync('outputs/motion-group1/asset-verification.json',JSON.stringify({reports,missing:reports.filter(r=>r.pending).map(r=>r.key),deviceVerified:false},null,2));console.log(JSON.stringify(reports));
