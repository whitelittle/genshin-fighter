// Read a map's real signal declarations; never create or rename map resources.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import assert from 'node:assert/strict';
import{decode,encode,msg,num,str,all,get,replace,number as N,bytes as B,message as M}from'../../work/node-gia-wire.mjs';
const args=process.argv.slice(2),arg=k=>args[args.indexOf(k)+1];
const mapFile=arg('--map'),input=arg('--graph'),out=arg('--out');assert(mapFile&&input&&out);
fs.mkdirSync(out,{recursive:true});
const mapBytes=fs.readFileSync(mapFile),mapRoot=decode(mapBytes.subarray(20,-4)),catalog=msg(mapRoot,10);
const sourceBytes=fs.readFileSync(input),sourceRoot=decode(sourceBytes.subarray(20,-4));
const sourceGraph=msg(msg(msg(msg(sourceRoot,1),13),1),1);
function information(data){const signalMeta=msg(data,107);const signal=[101,102,108].map(k=>str(msg(signalMeta,k),1)).find(Boolean);return{data,signal,kind:str(data,200),id:num(msg(msg(data,4),1),5)};}
const declarations=all(catalog,2).map(f=>information(msg(decode(f.v),1))).filter(d=>d.signal);
const existing=new Map();for(const d of declarations){const key=d.signal+':'+d.kind;assert(!existing.has(key),'Duplicate map declaration '+key);existing.set(key,d);}
const sourceDefs=new Map(all(sourceRoot,2).map(f=>{const unit=decode(f.v);return[num(msg(unit,1),4),information(msg(msg(msg(unit,14),1),1))];}));
const mutations=[];
let gf3=replace(sourceGraph,3,all(sourceGraph,3).map(f=>{
 let n=decode(f.v);const old=sourceDefs.get(num(msg(n,2),5));if(!old)return f;
 assert(old.signal.startsWith('GF3'));const target=existing.get(old.signal+':'+old.kind);assert(target,'Map signal missing: '+old.signal+':'+old.kind);
 const identity=msg(target.data,4);n=replace(n,2,[M(2,msg(identity,1))]);n=replace(n,3,[M(3,msg(identity,2))]);n=replace(n,9,[N(9,num(identity,5)||1)]);
 n=replace(n,4,all(n,4).map(pf=>{
  let p=decode(pf.v);const kind=num(msg(p,1),1),index=num(msg(p,1),2);
  if(kind===5){const meta=decode(all(target.data,106)[0].v);p=replace(p,3,[M(3,msg(msg(meta,4),2))]);p=replace(p,6,[M(6,msg(meta,5))]);p=replace(p,7,[N(7,num(meta,8))]);return M(4,p);}
  const section={1:100,2:101,3:102,4:103}[kind];if(!section)return pf;
  const oldPort=all(old.data,section).map(f=>decode(f.v)).find(q=>num(msg(q,3),2)===index);
  if(!oldPort)return pf;
  const name=str(oldPort,1),newPort=all(target.data,section).map(f=>decode(f.v)).find(q=>str(q,1)===name);
  assert(newPort,'Parameter missing: '+old.signal+'.'+name);assert.equal(num(msg(newPort,3),2),index,'Parameter order mismatch');
  if(kind===3||kind===4)assert.equal(num(msg(newPort,4),4),num(msg(oldPort,4),4),'Parameter type mismatch');
  p=replace(p,7,[N(7,num(newPort,8))]);return M(4,p);
 }));
 mutations.push({node:num(n,1),signal:target.signal,kind:target.kind,oldId:old.id,newId:target.id,version:num(identity,5)||1});return M(3,n);
}));
const gf2Candidates=all(catalog,1).map(f=>msg(decode(f.v),1)).filter(g=>str(g,2).startsWith('GFV2'));
assert.equal(gf2Candidates.length,1,'Expected original GFV2 graph in map');const gf2=gf2Candidates[0];
function unitFor(d){const meta=msg(d.data,107);const detail=[101,102,108].map(k=>msg(meta,k)).find(v=>v.length);const related=[2,3,4].map(k=>num(msg(detail,k),5)).filter(Boolean);
 return[M(1,[N(2,23),N(4,d.id)]),...related.map(id=>M(2,[N(2,23),N(4,id)])),B(3,d.kind),N(5,['发送信号','向服务器节点图发送信号'].includes(d.kind)?14:12),M(14,[M(1,[M(1,d.data)])])];}
function writeGraph(graph,title,includeDeclarations=false){
 const filename=title+'.gia',target=path.join(out,filename);assert(!fs.existsSync(target),'Refuse overwrite');
 const used=[...new Set(all(graph,3).map(f=>num(msg(decode(f.v),2),5)).filter(id=>declarations.some(d=>d.id===id)))];
 let unit=msg(sourceRoot,1);unit=replace(unit,1,[M(1,[N(2,5),N(4,num(msg(graph,1),5))])]);unit=replace(unit,2,used.map(id=>M(2,[N(2,23),N(4,id)])));unit=replace(unit,3,[B(3,title)]);
 graph=replace(graph,2,[B(2,title)]);unit=replace(unit,13,[M(13,[M(1,[M(1,graph)])])]);
 let root=sourceRoot.filter(f=>f.f!==2);root=replace(root,1,[M(1,unit)]);root=replace(root,3,[B(3,filename)]);
 if(includeDeclarations)root.push(...declarations.filter(d=>d.signal.startsWith(title.includes('GFV2')?'GFV2':'GF3')).map(d=>M(2,unitFor(d))));
 const payload=encode(root),header=Buffer.from(sourceBytes.subarray(0,20));header.writeUInt32BE(payload.length+20,0);header.writeUInt32BE(payload.length,16);
 const result=Buffer.concat([header,payload,sourceBytes.subarray(-4)]);fs.writeFileSync(target,result);
 return{filename,bytes:result.length,sha256:crypto.createHash('sha256').update(result).digest('hex'),nodes:all(graph,3).length,embeddedSignalDefinitions:all(root,2).length,requiredExistingSignals:used.map(id=>{const d=declarations.find(d=>d.id===id);return{id,signal:d.signal,kind:d.kind};})};
}
const files=[writeGraph(gf3,'gpt_20261013_GF3绑定地图已有命名信号'),writeGraph(gf2,'gpt_20261013_GFV2恢复原节点_引用已有信号')];
const validation=[writeGraph(gf3,'校验专用_GF3地图信号声明',true),writeGraph(gf2,'校验专用_GFV2地图信号声明',true)];
const report={sourceMapFilename:path.basename(mapFile),sourceMapSha256:crypto.createHash('sha256').update(mapBytes).digest('hex'),sameMapOnly:true,mapUnmodified:true,files,validation,mutations,nativeImportVerified:false};
fs.writeFileSync(path.join(out,'map-rebind.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({files,signalNodesRebound:mutations.length,existingSignalNames:[...new Set(mutations.map(m=>m.signal))]}));
