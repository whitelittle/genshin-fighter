import fs from 'node:fs';import{decode,msg,num,str,all,describe}from'./node-gia-wire.mjs';
const file='outputs/mobile-performance-20261013/gia/gpt_20261013_GF3车轮战_自带变量_结算关闭.gia';const b=fs.readFileSync(file),r=decode(b.subarray(20,-4)),g=msg(msg(msg(msg(r,1),13),1),1);
for(const f of all(g,3)){const n=decode(f.v),id=num(n,1);if([69,70,74,75,76].includes(id))console.log(JSON.stringify({id,type:describe(msg(n,2)),concrete:describe(msg(n,3)),pins:all(n,4).map(p=>describe(decode(p.v))),extra:n.filter(x=>x.f>6).map(x=>[x.f,x.w===0?Number(x.v):x.v.toString('hex')])}));}
