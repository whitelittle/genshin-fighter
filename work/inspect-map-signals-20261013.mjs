import fs from 'node:fs';
import {decode,encode} from './node-gia-wire.mjs';
const b=fs.readFileSync('C:/Users/Cheng/Desktop/111.gil');
const found=[];
function scan(fields,path,parents=[]){
 for(let i=0;i<fields.length;i++){
  const f=fields[i];if(f.w!==2)continue;
  const name=f.v.toString('utf8');
  if(/^(GF3|GFV2)[A-Za-z]+$/.test(name)){
   found.push({name,path:path+'.'+f.f+'['+i+']',parents:[...parents.slice(-2),fields].map(a=>a.map(x=>({field:x.f,wire:x.w,value:x.w===0?Number(x.v):x.w===2&&/^(GF3|GFV2)[A-Za-z]+$/.test(x.v.toString('utf8'))?x.v.toString('utf8'):undefined,bytes:x.w===2?x.v.length:undefined})))});
  }
  if(path.split('.').length>30)continue;
  try{const nested=decode(f.v);if(encode(nested).equals(f.v))scan(nested,path+'.'+f.f+'['+i+']',[...parents,fields]);}catch{}
 }
}
scan(decode(b.subarray(20,-4)),'root');
fs.mkdirSync('work/map-signal-inspection-20261013',{recursive:true});
fs.writeFileSync('work/map-signal-inspection-20261013/locations.json',JSON.stringify(found,null,2));
console.log(JSON.stringify(found.map(x=>({name:x.name,path:x.path,parent:x.parents.at(-1)})),null,2));
