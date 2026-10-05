import fs from 'node:fs';import assert from 'node:assert/strict';
import{decode,msg,num,str,all}from'./node-gia-wire.mjs';
const candidate='outputs/network-current-gia/'+JSON.parse(fs.readFileSync('outputs/network-current-gia/delivery.json')).filename;
const imported=process.argv[2]||'C:/Users/Cheng/Desktop/联机节点图4.gia';
function parse(file){const b=fs.readFileSync(file),root=decode(b.subarray(20,20+b.readUInt32BE(16))),graph=msg(msg(msg(msg(root,1),13),1),1),definitions=new Map();for(const f of all(root,2)){const a=decode(f.v),d=msg(msg(msg(a,14),1),1),s=msg(d,107);let signal='';for(const k of[101,102,108])signal ||=str(msg(s,k),1);definitions.set(num(msg(a,1),4),{signal,kind:str(a,3)});}return{nodes:new Map(all(graph,3).map(f=>{const n=decode(f.v);return[num(n,1),n];})),definitions};}
const before=parse(candidate),after=parse(imported),bindings={};assert.equal(before.nodes.size,after.nodes.size);
for(const[id,n]of before.nodes){const previous=before.definitions.get(num(msg(n,2),5));if(!previous?.signal)continue;const actual=after.definitions.get(num(msg(after.nodes.get(id),2),5));assert(actual&&actual.kind===previous.kind);assert(!bindings[previous.signal]||bindings[previous.signal]===actual.signal);bindings[previous.signal]=actual.signal;}
assert.equal(Object.keys(bindings).length,10);
fs.writeFileSync('work/network-signal-bindings.json',JSON.stringify(bindings,null,2));
for(const file of ['outputs/midphase-final/fighter.save.json','outputs/midphase-final/simulator.save.json']){
 const save=JSON.parse(fs.readFileSync(file));let source=save.assets.scripts[0].source;
 for(const[from,to]of Object.entries(bindings)){
  source=source.replaceAll("game.ServerSignal('"+from+"')","game.ServerSignal('"+to+"')");
  source=source.replaceAll("script:RegisterServerSignalHandler('"+from+"'","script:RegisterServerSignalHandler('"+to+"'");
 }
 save.assets.scripts[0].source=source;
 if(file.endsWith('simulator.save.json')){
  function rewrite(v){if(!v||typeof v!=='object')return;for(const[k,x]of Object.entries(v)){if(k==='signalName'&&bindings[x])v[k]=bindings[x];else rewrite(x);}}
  rewrite(save.serverLogic);
 }
 fs.writeFileSync(file,JSON.stringify(save));
}
console.log(JSON.stringify(bindings));
