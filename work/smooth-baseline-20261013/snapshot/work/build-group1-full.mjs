import{readFileSync,writeFileSync,mkdirSync}from'node:fs';import{execFileSync}from'node:child_process';import assert from'node:assert/strict';import{loadGroup1Set}from'./group1-sets.mjs';
const out=process.env.GROUP1_OUT||'outputs/group1-full-test';mkdirSync(out,{recursive:true});
let code=readFileSync('work/build-roster-v2.mjs','utf8');
code="import{loadGroup1Set}from'./group1-sets.mjs';\n"+code;
code=code.replace("const out='outputs/roster-v2'",`const out='${out}'`);
if(process.env.FINAL_ROSTER==='19')code=code.replace("const roster=all.filter(([key],i)=>i<11||existsSync(`assets/roster-v2/${key}-frames.json`));", "const active=new Set([...JSON.parse(readFileSync('outputs/motion-production/batch-plan.json')).samples,...JSON.parse(readFileSync('outputs/motion-production/batch-plan.json')).batches[0].roles].map(r=>r[0]));const roster=all.filter(r=>active.has(r[0]));assert.equal(roster.length,19);");
code=code.replace('const sets=roster.map(','const legacySets=roster.map(');
const at=code.indexOf('\nconst headsAll=');assert(at>0);
code=code.slice(0,at)+"\nconst sets=roster.map(([key],i)=>loadGroup1Set(key,legacySets[i]));\n"+code.slice(at);
writeFileSync('work/build-group1-full-generated.mjs',code);execFileSync(process.execPath,['work/build-group1-full-generated.mjs'],{stdio:'inherit'});
const save=JSON.parse(readFileSync(out+'/base.save.json','utf8')),roster=JSON.parse(readFileSync(out+'/roster.json','utf8'));
const motions=[],aliases=[],upgraded=[];
for(const[key]of roster){const r=loadGroup1Set(key,null);if(!r)continue;const id=roster.findIndex(x=>x[0]===key)+1;
 motions.push(`[${id}]={idle={${r.motion.idle.map(x=>`{${x}}`).join(',')}},walk={${r.motion.walk.map(x=>`{${x}}`).join(',')}}}`);
 for(const[name,idx]of Object.entries(r.aliases))aliases.push(`poseIds[${id}][${JSON.stringify(name)}]=${idx}`);
 upgraded.push({key,id,frames:r.frames.length,pool:r.pool,source:r.source});
}
let source=save.assets.scripts[0].source;const marker='local function updateSprite(i)';assert(source.includes(marker));
source=source.replace(marker,'local group1Motion={'+motions.join(',')+'}\n'+aliases.join('\n')+'\n'+readFileSync('work/group1-motion-runtime.lua','utf8')+'\n'+marker);
assert(source.includes('pose=pose or ids.idle'));source=source.replace('pose=pose or ids.idle','pose=group1Pose(a,i)or pose or ids.idle');
save.assets.scripts[0].source=source;
function visit(n){if(n.kind==='text'&&/重新选|重选角色|重选阵容/.test(n.text||''))n.text='返回选人';for(const c of n.children||[])visit(c);}
visit(save.assets.server.root);save.meta.name='原神格斗 · 第一批完整测试';
writeFileSync(out+'/base.save.json',JSON.stringify(save));writeFileSync(out+'/motion-integration.json',JSON.stringify({upgraded,reusedLawachurl:'assets/roster-v2/lawachurl-frames.json',optimizedLoading:true,frameTiming:'derived from simulation attack phase; no image callback',deviceVerified:false},null,2));
console.log('GROUP1_FULL_MOTION',upgraded.length);
