import fs from 'node:fs';import{decode,encode,msg,num,all,get,replace,message as M,number as N,bytes as B}from'./node-gia-wire.mjs';
const original=fs.readFileSync('C:/Users/Cheng/Desktop/联机节点图4.gia');let r=decode(original.subarray(20,20+original.readUInt32BE(16)));
const d=JSON.parse(fs.readFileSync('outputs/network-current-gia/delivery.json'));const generated=fs.readFileSync('outputs/network-current-gia/'+d.filename),oldRoot=decode(generated.subarray(20,20+generated.readUInt32BE(16)));
const graphOf=r=>msg(msg(msg(msg(r,1),13),1),1),before=new Map(all(graphOf(oldRoot),3).map(x=>{const n=decode(x.v);return[num(n,1),n];}));
let graph=graphOf(r);const fixes=[];
graph=replace(graph,3,all(graph,3).map(x=>{
 let n=decode(x.v);const source=before.get(num(n,1));
 n=replace(n,4,all(n,4).map(y=>{
  let p=decode(y.v);const k=num(msg(p,1),1),i=num(msg(p,1),2),oldPin=all(source,4).map(x=>decode(x.v)).find(q=>num(msg(q,1),1)===k&&num(msg(q,1),2)===i),v=oldPin&&msg(oldPin,3);
  if(k===3&&v&&num(p,4)===3&&!get(p,5)&&(get(v,102)||get(msg(msg(v,110),2),102))){
   const rawValue=get(msg(get(v,110)?msg(msg(v,110),2):v,102),1)?.v||0n;
   const desired=Number(BigInt.asIntN(32,rawValue));
   let literal=msg(p,3),inner=get(literal,110)?msg(msg(literal,110),2):literal;
   const current=num(msg(inner,102),1),state=num(inner,2);
   inner=replace(replace(inner,102,[M(102,desired?[N(1,desired)]:[])]),2,[N(2,1)]);
   literal=get(literal,110)?replace(literal,110,[M(110,replace(msg(literal,110),2,[M(2,inner)]))]):inner;
   p=replace(p,3,[M(3,literal)]);
   if(desired!==current||state!==1)fixes.push({node:num(n,1),input:i,before:current,after:desired,literalState:1});
  }
  return M(4,p);
 }));return M(3,n);
}));
let unit=msg(r,1),wrap=msg(unit,13),wrap1=msg(wrap,1);wrap1=replace(wrap1,1,[M(1,graph)]);wrap=replace(wrap,1,[M(1,wrap1)]);unit=replace(unit,13,[M(13,wrap)]);r=replace(r,1,[M(1,unit)]);r=replace(r,3,[B(3,'常量修正校验.gia')]);
const payload=encode(r),header=Buffer.from(original.subarray(0,20));header.writeUInt32BE(payload.length+20,0);header.writeUInt32BE(payload.length,16);const corrected=Buffer.concat([header,payload,original.subarray(-4)]);
fs.writeFileSync('outputs/network-node-sample4/常量修正校验.gia',corrected);fs.writeFileSync('outputs/network-node-sample4/constants-fixes.json',JSON.stringify(fixes,null,2));console.log(JSON.stringify(fixes));
