import fs from 'node:fs';import crypto from 'node:crypto';import assert from 'node:assert/strict';
import{decode,encode,msg,num,all,replace,message as M,number as N,bytes as B}from'./node-gia-wire.mjs';
const out='outputs/network-import-fix';fs.mkdirSync(out,{recursive:true});
const source=fs.readFileSync('outputs/network-node-sample4/常量修正校验.gia');let root=decode(source.subarray(20,20+source.readUInt32BE(16)));
const stamp=new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(new Date()).replace(/[-: ]/g,'').replace(/^(\d{8})(\d{6})$/,'$1_$2');
const title='gpt_'+stamp+'_联机节点_常量修复_引用现有信号',filename=title+'.gia',graphId=1073741928;
let unit=msg(root,1),wrap=msg(unit,13),wrap1=msg(wrap,1),graph=msg(wrap1,1);
graph=replace(graph,1,[M(1,replace(msg(graph,1),5,[N(5,graphId)]))]);graph=replace(graph,2,[B(2,title)]);
unit=replace(unit,1,[M(1,replace(msg(unit,1),4,[N(4,graphId)]))]);unit=replace(unit,3,[B(3,title)]);
wrap1=replace(wrap1,1,[M(1,graph)]);wrap=replace(wrap,1,[M(1,wrap1)]);unit=replace(unit,13,[M(13,wrap)]);root=replace(root,1,[M(1,unit)]);root=replace(root,3,[B(3,filename)]);
// Same-project repair: reference current imported signal resources rather than importing duplicate definitions.
const existingDefs=new Set(all(root,2).map(x=>num(msg(decode(x.v),1),4)));
const required=all(unit,2).map(x=>num(decode(x.v),4));assert(required.every(id=>existingDefs.has(id)));assert.equal(required.length,10);
root=root.filter(x=>x.f!==2);
const payload=encode(root),header=Buffer.from(source.subarray(0,20));header.writeUInt32BE(payload.length+20,0);header.writeUInt32BE(payload.length,16);const bytes=Buffer.concat([header,payload,source.subarray(-4)]);
fs.writeFileSync(out+'/'+filename,bytes);
const d={stamp,filename,bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),graphId,signalBindings:JSON.parse(fs.readFileSync('work/network-signal-bindings.json')),requiredExistingResourceIds:required,embeddedSignalDefinitions:0,fixes:JSON.parse(fs.readFileSync('outputs/network-node-sample4/constants-fixes.json')),sameProjectOnly:true,officialImportVerified:false};
fs.writeFileSync(out+'/delivery.json',JSON.stringify(d,null,2));console.log(JSON.stringify({filename,bytes:bytes.length,fixes:d.fixes.length,sameProjectOnly:true,officialImportVerified:false}));
