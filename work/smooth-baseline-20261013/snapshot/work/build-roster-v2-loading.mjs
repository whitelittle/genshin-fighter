import{readFileSync,writeFileSync}from'node:fs';
// Reuse the validated GIA/template exporter, but store pool recipes rather than thousands of duplicate placeholder rows.
let code=readFileSync('work/build-duel-loading.mjs','utf8');
code=code.replace("const jobs=[];","const jobs=save._pixelJobs||[];");
const start=code.indexOf("const data='local loadingJobs={"),end=code.indexOf("let source=save.assets.scripts[0].source;",start);
code=code.slice(0,start)+`const data='local loadingJobs={'+jobs.map(j=>'{path={'+j.path.map(luaString).join(',')+'},prefix='+luaString(j.prefix)+',count='+j.count+'}').join(',')+'}\\nlocal loadingPaimonFrames={'+paimon.map(luaFrame).join(',')+'}\\n';\n`+code.slice(end);
code=code.replace("jobs.reduce((a,j)=>a+j.rows.length,0)","jobs.reduce((a,j)=>a+(j.count||j.rows?.length||0),0)");
code=code.replace("save.assets.scripts[0].source=source;","delete save._pixelJobs;save.assets.scripts[0].source=source;");
writeFileSync('work/build-roster-v2-loading-generated.mjs',code);
let runtime=readFileSync('work/v2-loading.lua','utf8');runtime=runtime.replace('#job.rows','job.count').replace("local row=loadingJobs[j].rows[n];loadingRegistry[loadingKey(parent)][row[1]]=nil","local name=loadingJobs[j].prefix..n;loadingRegistry[loadingKey(parent)][name]=nil").replace("local row=loadingJobs[j].rows[n]","local name=loadingJobs[j].prefix..n").replaceAll('row[1]','name');writeFileSync('work/v2-loading-generated.lua',runtime);
console.log('POOL_RECIPES_READY');
