import fs from'node:fs';import path from'node:path';import assert from'node:assert/strict';import crypto from'node:crypto';
import{decode,encode,msg,num,str,all,get,replace,message as M}from'../../work/node-gia-wire.mjs';
const args=process.argv.slice(2),arg=k=>args[args.indexOf(k)+1];
const input=arg('--input'),reference=arg('--reference'),out=arg('--out');assert(input&&reference&&out);
function read(file){const bytes=fs.readFileSync(file),root=decode(bytes.subarray(20,-4)),graph=msg(msg(msg(msg(root,1),13),1),1),defs=new Map();
 for(const f of all(root,2)){const unit=decode(f.v),data=msg(msg(msg(unit,14),1),1),s=msg(data,107);let name='';for(const k of[101,102,108])name||=str(msg(s,k),1);if(name)defs.set(num(msg(unit,1),4),{name,kind:str(unit,3)});}
 return{bytes,root,graph,defs,nodes:new Map(all(graph,3).map(x=>{const n=decode(x.v);return[num(n,1),n]}))};}
const before=read(input),ref=read(reference),bindings=new Map();assert.equal(before.nodes.size,ref.nodes.size,'exported graph is not the supplied GF3 revision');
for(const[id,n]of ref.nodes){const expected=ref.defs.get(num(msg(n,2),5)),actualNode=before.nodes.get(id);assert(actualNode,'node ID changed: '+id);
 if(!expected){assert.equal(num(msg(actualNode,2),5),num(msg(n,2),5),'builtin node changed: '+id);continue;}
 const actual=before.defs.get(num(msg(actualNode,2),5));assert(actual&&actual.kind===expected.kind,'signal node mismatch: '+id);
 assert(!bindings.has(actual.name)||bindings.get(actual.name)===expected.name,'ambiguous imported signal name');bindings.set(actual.name,expected.name);
}
assert.equal(new Set(bindings.values()).size,12,'must identify all twelve signals');
let changes=0;
function rewrite(fields){return fields.map(f=>{if(f.w!==2)return f;const name=f.v.toString('utf8');if(bindings.has(name)&&bindings.get(name)!==name){changes++;return{...f,v:Buffer.from(bindings.get(name))};}
 try{const nested=decode(f.v);if(!encode(nested).equals(f.v))return f;const prior=changes;const updated=rewrite(nested);return prior===changes?f:{...f,v:encode(updated)};}catch{return f;}
});}
const keepImportedNames=args.includes('--keep-imported-names');
let updated=keepImportedNames?before.root:rewrite(before.root);const constantFixes=[];
let unit=msg(updated,1),wrap=msg(unit,13),inner=msg(wrap,1),graph=msg(inner,1);
graph=replace(graph,3,all(graph,3).map(f=>{
 let node=decode(f.v);const id=num(node,1),expected=ref.nodes.get(id);
 node=replace(node,4,all(node,4).map(f=>{
  let p=decode(f.v);const kind=num(msg(p,1),1),index=num(msg(p,1),2);
  if(kind!==3||get(p,5))return f;
  const rp=all(expected,4).map(x=>decode(x.v)).find(q=>num(msg(q,1),1)===kind&&num(msg(q,1),2)===index);
  if(!rp||get(rp,5)||!get(rp,3))return f;
  const value=msg(rp,3),base=get(value,110)?msg(msg(value,110),2):value;
  if(num(base,2)!==1)return f;
  if(!get(p,3)||!get(p,3).v.equals(get(rp,3).v)){
   constantFixes.push({node:id,input:index,type:num(rp,4)});p=replace(p,3,[M(3,value)]);
  }
  return M(4,p);
 }));return M(3,node);
}));
inner=replace(inner,1,[M(1,graph)]);wrap=replace(wrap,1,[M(1,inner)]);unit=replace(unit,13,[M(13,wrap)]);updated=replace(updated,1,[M(1,unit)]);
const payload=encode(updated),head=Buffer.from(before.bytes.subarray(0,20));head.writeUInt32BE(payload.length+20,0);head.writeUInt32BE(payload.length,16);
const result=Buffer.concat([head,payload,before.bytes.subarray(-4)]);fs.mkdirSync(path.dirname(out),{recursive:true});assert(!fs.existsSync(out),'refuse overwrite');fs.writeFileSync(out,result);
const after=read(out);assert.deepEqual([...after.nodes.keys()],[...before.nodes.keys()]);
for(const[id,n]of after.nodes){const d=after.defs.get(num(msg(n,2),5));if(d){const previous=before.defs.get(num(msg(before.nodes.get(id),2),5));assert.equal(d.name,keepImportedNames?previous.name:bindings.get(previous.name));}}
assert(get(after.root,3).v.equals(get(before.root,3).v),'opaque export identity changed');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const report={sourceFilename:path.basename(input),sourceSha256:sha(before.bytes),filename:path.basename(out),sha256:sha(result),nodes:after.nodes.size,replacements:changes,bindings:Object.fromEntries(bindings),constantFixes,graphAndFunctionIdsPreserved:true,opaqueExportIdentityPreserved:true,nativeImportVerified:false};
fs.writeFileSync(path.join(path.dirname(out),'signal-name-correction.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
