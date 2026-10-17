import fs from 'node:fs';import assert from 'node:assert/strict';
import{decode,msg,num,str,all,get}from'../../work/node-gia-wire.mjs';
const args=process.argv.slice(2),file=args[0];assert(file,'GIA path required');
const source=fs.readFileSync('work/node-api-reference/concrete_map.ts','utf8');
const json=s=>JSON.parse(s.replace(/\/\/[^\n]*/g,'').replace(/'([^']*)'/g,(_,x)=>JSON.stringify(x)).replace(/,\s*([\]}])/g,'$1'));
const maps=json(source.match(/maps:\s*(\[[\s\S]*?\]),\s*pins:/)[1]);
const mappings=new Map(json(source.match(/pins:\s*new Map\((\[[\s\S]*?\])\)/)[1]));
const bytes=fs.readFileSync(file),root=decode(bytes.subarray(20,-4)),graph=msg(msg(msg(msg(root,1),13),1),1);
const nodes=new Map(all(graph,3).map(f=>{const n=decode(f.v);return[num(n,1),n]}));const errors=[];let checked=0;
for(const[id,n]of nodes){const type=num(msg(n,2),5);
 for(const f of all(n,4)){
  const p=decode(f.v),kind=num(msg(p,1),1),index=num(msg(p,1),2),map=mappings.get(type+':'+kind+':'+index);
  if(map!==undefined){checked++;const raw=msg(p,3),selected=num(msg(raw,110),1),want=num(p,4);
   if(num(raw,1)!==10000)errors.push({node:id,kind,index,type,reason:'reflective pin missing ConcreteBase wrapper'});
   else if(maps[map][selected]!==want)errors.push({node:id,kind,index,type,reason:'concrete index/type mismatch',selected,actual:maps[map][selected],want});
  }
  const link=msg(p,5);if(link.length){const target=num(link,1);if(!nodes.has(target))errors.push({node:id,target,reason:'dangling connection'});}
 }
}
// Graph variable nodes must use their own port layout and selected concrete type.
for(const[id,n]of nodes){const type=num(msg(n,2),5),concrete=num(msg(n,3),5),pins=all(n,4).map(x=>decode(x.v));
 const at=(kind,index)=>pins.find(p=>num(msg(p,1),1)===kind&&num(msg(p,1),2)===index);
 if(type===323){const p=at(3,1),t=p&&num(p,4);assert(p,'missing setter value');if(concrete!==(t===1?328:323))errors.push({node:id,reason:'setter concrete id mismatch'});}
 if(type===337){const p=at(4,0),t=p&&num(p,4);assert(p,'missing getter output');if(concrete!==(t===1?337:339))errors.push({node:id,reason:'getter concrete id mismatch'});}
}
const report={file:file.split(/[\\/]/).pop(),reflectivePinsChecked:checked,errors,nativeEditorValidation:false};
console.log(JSON.stringify(report));if(args.includes('--report'))fs.writeFileSync(args[args.indexOf('--report')+1],JSON.stringify(report,null,2));
if(errors.length)process.exitCode=1;
