import{readFileSync,existsSync}from'node:fs';
const routes={kaeya:'kaeya',yanfei:'yanfei',klee:'klee-approved-v3'};
export function loadGroup1Set(key,fallback){
 const root='outputs/motion-group1/'+(process.env.FINAL_ART==='1'&&key==='kamisatoayaka'?'kamisatoayaka-final':routes[key]||key);
 if(!existsSync(root+'/manifest.json'))return fallback;
 const r=JSON.parse(readFileSync(root+'/manifest.json','utf8')).roles[0];
 if(existsSync(root+'/弃用标记.json')){
  const rejected=JSON.parse(readFileSync(root+'/弃用标记.json','utf8')).files||[];
  for(const f of r.frames)if(rejected.includes(f.source))throw Error('Rejected source cannot enter test package: '+key+'/'+f.source);
 }
 const data=JSON.parse(readFileSync(root+`/data/${key}.json`,'utf8'));
 if(r.frames.length<48)throw Error('Incomplete group1 frames '+key);
 const frames=data.frames.map(f=>({...f,pose:f.id,scale:f.scale*(key==='klee'?1.2:1)}));
 const names={idle:'basic0',idle2:'basic1',walk1:'basic2',walk2:'basic4',crouch:'basic5',guard:'basic6',crouchGuard:'basic7',jump:'basic9',hurt:'basic12',airHurt:'basic13',down:'basic14',getup:'basic15',windup:'attack0',slash:'attack1',low:'attack4',air:'attack7',rising:'attack7',special:'attack9',eThrow:'attack8',e1:'attack9',e2:'attack9',e3:'attack9',e3Windup:'attack8',teleport:'attack9',qCharge:'attack11',qRelease:'attack12'};
 const aliases=Object.fromEntries(Object.entries(names).map(([name,id])=>[name,frames.findIndex(f=>f.id===id)+1]));
 const indices=Object.fromEntries(frames.map((f,i)=>[f.id,i+1]));
 return{role:key,frames,pool:r.pool,motion:{idle:r.sequences.idle.map(([id,n])=>[indices[id],n]),walk:r.sequences.walk.map(([id,n])=>[indices[id],n])},aliases,source:root};
}
