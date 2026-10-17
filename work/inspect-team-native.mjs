import fs from 'node:fs';
import{decode,msg,num,str,all,describe}from'./node-gia-wire.mjs';
const b=fs.readFileSync('outputs/network-current-gia/gpt_20261004_165104_19角色完整联机节点.gia');const root=decode(b.subarray(20,-4));
for(const f of all(root,2)){
 const def=decode(f.v),d=msg(msg(msg(def,14),1),1),s=msg(d,107);
 let signal='';for(const n of [101,102,108])signal||=str(msg(s,n),1);
 if(signal==='FighterTeam'&&str(def,3)==='监听信号')console.log(JSON.stringify({data:describe(d.filter(x=>[4,200,203,204].includes(x.f)))}));
}
