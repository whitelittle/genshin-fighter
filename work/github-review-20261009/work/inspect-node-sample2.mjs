import{readFileSync,writeFileSync}from'node:fs';import{decode,encode,msg,num,str,all,describe}from'./node-gia-wire.mjs';
const b=readFileSync('C:/Users/Cheng/Desktop/联机节点图2.gia');const root=decode(b.subarray(20,20+b.readUInt32BE(16)));if(!encode(root).equals(b.subarray(20,20+b.readUInt32BE(16))))throw Error('Roundtrip mismatch');
const main=msg(msg(msg(msg(root,1),13),1),1),nodes=all(main,3).map(x=>decode(x.v));
const accessories=all(root,2).map(x=>decode(x.v));
console.log(JSON.stringify({nodeCount:nodes.length,accessories:accessories.map(a=>({id:num(msg(a,1),4),name:str(a,3),fields:a.map(x=>x.f)})),newNodes:nodes.filter(n=>num(n,1)>=46).map(describe)},null,2));
writeFileSync('outputs/network-node-sample2/schema-roundtrip.json',JSON.stringify({losslessWireRoundtrip:true,nodeCount:nodes.length,accessoryCount:accessories.length},null,2));
