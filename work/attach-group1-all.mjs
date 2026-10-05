import{readFileSync,writeFileSync,existsSync}from'node:fs';
const batch=JSON.parse(readFileSync('outputs/motion-production/batch-plan.json','utf8')).batches[0].roles;
const rows=[];
for(const[key]of batch){const folder=key==='klee'?'klee-approved-v3':key,root='outputs/motion-group1/'+folder;
 if(!existsSync(root+'/manifest.json'))continue;
 const r=JSON.parse(readFileSync(root+'/manifest.json','utf8')).roles[0];
 if(existsSync(root+'/弃用标记.json')){const rejected=JSON.parse(readFileSync(root+'/弃用标记.json','utf8')).files||[];if(r.frames.some(f=>rejected.includes(f.source)))continue;}
 r.visualKey=key;r.key=key+'-group1-current';r.frames.forEach(f=>f.png='../motion-group1/'+folder+'/'+f.png);rows.push(r);
}
if(process.env.FINAL_ART==='1'){
 const root='outputs/motion-group1/kamisatoayaka-final',r=JSON.parse(readFileSync(root+'/manifest.json','utf8')).roles[0];
 r.visualKey='kamisatoayaka';r.key='kamisatoayaka-final';r.frames.forEach(f=>f.png='../motion-group1/kamisatoayaka-final/'+f.png);rows.push(r);
}
writeFileSync('outputs/motion-group1/all-addon.js','window.GROUP1_ROLES='+JSON.stringify(rows)+';window.MOTION_PRODUCTION.roles.push(...window.GROUP1_ROLES);');
let page=readFileSync('outputs/motion-production/index.html','utf8');page=page.replace(/<script src="\.\.\/motion-group1\/[^\"]+\/addon\.js"><\/script>/g,'');if(!page.includes('../motion-group1/all-addon.js'))page=page.replace('<script src="model.js">','<script src="../motion-group1/all-addon.js"></script><script src="model.js">');page=page.replaceAll('五角色动作制作探针','角色动作制作探针').replace('MOTION PRODUCTION · FIVE SAMPLES','MOTION PRODUCTION · GROUP 1');writeFileSync('outputs/motion-production/index.html',page);
let script=readFileSync('outputs/motion-production/probe.js','utf8');script=script.replace("r.key==='klee-group1-v2'","r.visualKey==='klee'");writeFileSync('outputs/motion-production/probe.js',script);console.log('GROUP1_PROBE',rows.length);
