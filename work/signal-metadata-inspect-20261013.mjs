import fs from'node:fs';import{decode,encode,msg,num,str,all,describe}from'./node-gia-wire.mjs';
for(const file of ['outputs/network-current-gia/gpt_20261004_165104_19角色完整联机节点.gia','outputs/native-port-fix-20261013/gpt_20261013_GF3车轮战_端口修正版.gia','C:/Users/Cheng/Desktop/联机节点图4.gia']){
 if(!fs.existsSync(file))continue;const b=fs.readFileSync(file),r=decode(b.subarray(20,-4));
 const defs=all(r,2).map(f=>decode(f.v));
 console.log(file.split(/[\\/]/).pop(),JSON.stringify(r.map(x=>[x.f,x.w,x.w===2?x.v.length:Number(x.v)])));
 for(const def of defs.slice(0,4)){const data=msg(msg(msg(def,14),1),1);console.log(JSON.stringify({unitHeader:def.filter(f=>f.f!==14).map(f=>[f.f,f.w===2?(f.f===3?f.v.toString('utf8'):describe(decode(f.v))):Number(f.v)]),signalMeta:describe(msg(data,107)),dataFields:data.map(x=>[x.f,x.w,x.w===2?x.v.length:Number(x.v)])}));}
}
