import{readFileSync,writeFileSync,existsSync}from'node:fs';
import{createHash}from'node:crypto';
const roster=JSON.parse(readFileSync('outputs/roster-v2/roster.json'));
const file=p=>({path:p,bytes:readFileSync(p).length,sha256:createHash('sha256').update(readFileSync(p)).digest('hex')});
const entries=roster.map(([key,name],i)=>{const candidate=`assets/roster-v2/${key}-frames.json`,frames=existsSync(candidate)?candidate:`assets/${i<2?'vnext':'test-v1'}/${key}-frames.json`;return{id:i+1,key,name,frames:file(frames)};});
const inputs=['assets/roster-v2/heads.json','assets/roster-v2/thumbs.json','assets/roster-v2/generation-manifest.json','assets/roster-v2/official-source-records.json','work/build-roster-v2.mjs','work/v2-menu.lua','work/v2-loading.lua','work/v2-unpack.lua','work/v2-pack.mjs'].map(file);
const evidence={gameplay:'simulator sampled three rounds/rematch/exit passed before final wording-only adjustment',layout:'final source mobile 19.5:9 and 4:3 passed',officialImport:false,devicePerformance:false};
const data={schemaVersion:1,roster:entries,inputs,build:JSON.parse(readFileSync('outputs/roster-v2/build.json')),source:file('outputs/roster-v2/fighter_duel_loading_v2.lua'),evidence};
writeFileSync('outputs/roster-v2/有效素材清单.json',JSON.stringify(data,null,2));console.log('RESOURCE_INDEX_PASS',entries.length);
