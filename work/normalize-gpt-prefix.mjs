import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const root=process.cwd();
const external=process.argv.includes('--external');
const scope=external?'C:/Users/Cheng/AppData/LocalLow/miHoYo/原神/BeyondLocal/Beyond_Local_Export':root;
const backup=path.join(root,'outputs/prefix-rename-backup',external?'external':'workspace');
const extensions=new Set(['.md','.txt','.rst','.json','.mjs','.js','.ps1','.lua','.html','.gia']);
const skip=new Set(['.git','node_modules','.agents','.codex','prefix-rename-backup']);
const files=[];
function walk(dir){for(const e of fs.readdirSync(dir,{withFileTypes:true})){if(skip.has(e.name)||e.name==='normalize-gpt-prefix.mjs')continue;const f=path.join(dir,e.name);if(e.isDirectory())walk(f);else files.push(f);}}
walk(scope);
const changes=[];
const hashMap=new Map();
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function recoverHashes(dir){if(!fs.existsSync(dir))return;for(const e of fs.readdirSync(dir,{withFileTypes:true})){const f=path.join(dir,e.name);if(e.isDirectory())recoverHashes(f);else if(/\.(gia|lua)\.bak$/.test(e.name)){const b=fs.readFileSync(f),n=Buffer.from(b);for(let i=0;i<n.length-2;i++)if(n[i]===103&&n[i+1]===116&&n[i+2]===112){n[i+1]=112;n[i+2]=116;i+=2;}hashMap.set(hash(b),hash(n));}}}
recoverHashes(backup);
for(const file of files){
 const rename=path.basename(file).startsWith('gtp')?path.join(path.dirname(file),path.basename(file).replace(/^gtp/,'gpt')):file;
 if(rename!==file&&fs.existsSync(rename))throw Error('名称冲突，停止：'+rename);
 let original=null,updated=null;
 if(extensions.has(path.extname(file).toLowerCase())){
  original=fs.readFileSync(file);
  if(original.includes(Buffer.from('gtp'))){
   // Three ASCII bytes stay three bytes: protobuf lengths and other binary fields remain intact.
   updated=Buffer.from(original);
   for(let i=0;i<updated.length-2;i++)if(updated[i]===103&&updated[i+1]===116&&updated[i+2]===112){updated[i+1]=112;updated[i+2]=116;i+=2;}
   if(path.extname(file).toLowerCase()==='.gia'&&original.length!==updated.length)throw Error('GIA长度改变');
   hashMap.set(hash(original),hash(updated));
  }
 }
 if(rename!==file||updated)changes.push({file,rename,original,updated});
}
// Refresh hashes that describe changed GIA/Lua assets; original source samples are untouched.
for(const file of files.filter(f=>path.extname(f).toLowerCase()==='.json')){
 let change=changes.find(c=>c.file===file);
 let original=change?.original??fs.readFileSync(file);
 let text=(change?.updated??original).toString('utf8');
 let replaced=text.replace(/\b[a-fA-F0-9]{64}\b/g,s=>hashMap.get(s.toLowerCase())??s);
 if(replaced!==text){if(!change){change={file,rename:file,original,updated:null};changes.push(change);}change.updated=Buffer.from(replaced);}
}
fs.mkdirSync(backup,{recursive:true});
for(const change of changes){
 const saved=path.join(backup,path.relative(scope,change.file)+'.bak');
 if(fs.existsSync(saved))continue;
 fs.mkdirSync(path.dirname(saved),{recursive:true});
 fs.copyFileSync(change.file,saved);
}
for(const change of changes){
 if(change.updated)fs.writeFileSync(change.file,change.updated);
 if(change.rename!==change.file)fs.renameSync(change.file,change.rename);
 if(change.updated&&hash(fs.readFileSync(change.rename))!==hash(change.updated))throw Error('写入校验失败');
}
const report={scope:external?'千星导出目录':'项目工作区',renamed:changes.filter(c=>c.rename!==c.file).length,contentsUpdated:changes.filter(c=>c.updated).length,files:changes.map(c=>({before:path.relative(scope,c.file),after:path.relative(scope,c.rename)}))};
fs.writeFileSync(path.join(backup,'report.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({scope:report.scope,renamed:report.renamed,contentsUpdated:report.contentsUpdated,backup:path.relative(root,backup)}));
