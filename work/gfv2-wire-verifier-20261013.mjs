import fs from 'node:fs';import assert from 'node:assert/strict';import crypto from 'node:crypto';
import{decode,encode,msg,num,str,all,get}from'./node-gia-wire.mjs';
const out=process.argv.includes('--out')?process.argv[process.argv.indexOf('--out')+1]:'outputs/team-battle-20261013',file=out+'/'+(process.argv.includes('--file')?process.argv[process.argv.indexOf('--file')+1]:(process.argv.includes('--new')?'gpt_20261013_GF3车轮战_自带变量_结算关闭.gia':'gpt_20261013_三人车轮战_GF3独立节点.gia')),b=fs.readFileSync(file),r=decode(b.subarray(20,-4));
assert.equal(b.readUInt32BE(0),b.length-4);assert.equal(b.readUInt32BE(16),b.length-24);assert(encode(r).equals(b.subarray(20,-4)));
const graph=msg(msg(msg(msg(r,1),13),1),1),nodes=new Map(all(graph,3).map(x=>{const n=decode(x.v);return[num(n,1),n];})),defs=new Map();
const definitionFile=process.argv.includes('--definition-source')?process.argv[process.argv.indexOf('--definition-source')+1]:null;
const definitionRoot=definitionFile?decode(fs.readFileSync(definitionFile).subarray(20,-4)):r;
const bindingFile=process.argv.includes('--signal-bindings')?process.argv[process.argv.indexOf('--signal-bindings')+1]:null;
const logicalNames=bindingFile?Object.fromEntries(Object.entries(JSON.parse(fs.readFileSync(bindingFile,'utf8'))).map(([logical,actual])=>[actual,logical])):{};
for(const f of all(definitionRoot,2)){const def=decode(f.v),data=msg(msg(msg(def,14),1),1),s=msg(data,107);let signal='';for(const k of[101,102,108])signal||=str(msg(s,k),1);signal=logicalNames[signal]||signal;defs.set(num(msg(def,1),4),{signal,kind:str(def,3),data});}
const pin=(n,kind,index=0)=>all(n,4).map(x=>decode(x.v)).find(p=>num(msg(p,1),1)===kind&&num(msg(p,1),2)===index);
for(const n of nodes.values())for(const f of all(n,4)){const p=decode(f.v),link=msg(p,5);if(link.length)assert(nodes.has(num(link,1)),'dangling edge');}
const entries={};for(const[id,n]of nodes){const d=defs.get(num(msg(n,2),5));if(d?.kind==='监听信号')entries[d.signal]=id;}
const state={},players=[301,502];let event={},sent=[],settlements=0;
for(const f of all(graph,6)){const v=decode(f.v),raw=msg(v,4);state[str(v,2)]=Number(BigInt.asIntN(32,get(msg(raw,num(v,3)===1?101:102),1)?.v||0n));}
function data(n,k,i=0){const p=pin(n,k,i);assert(p,[num(n,1),k,i]);const link=msg(p,5);if(link.length)return output(nodes.get(num(link,1)),num(msg(link,2),2));
 const raw=msg(p,3);if(get(raw,105))return str(msg(raw,105),1);const v=get(raw,110)?msg(msg(raw,110),2):raw;return Number(BigInt.asIntN(64,get(msg(v,102),1)?.v||0n));}
function output(n,index=0){const type=num(msg(n,2),5),d=defs.get(type);
 if(d?.kind==='监听信号'){const p=all(d.data,103).map(x=>decode(x.v)).find(p=>num(msg(p,3),2)===index);return event.params[str(p,1)];}
 if(type===73)return'controller';if(type===248)return players;if(type===142)return data(n,3,0).length;if(type===128)return data(n,3,0)[data(n,3,1)];
 if(type===50)return state[data(n,3,1)]??0;if(type===337)return state[data(n,3,0)]??0;if(type===14)return data(n,3,0)===data(n,3,1);if(type===232)return data(n,3,0)>data(n,3,1);if(type===233)return data(n,3,0)>=data(n,3,1);
 throw Error('unsupported data '+type);
}
function next(n,index=0){const p=pin(n,2,index);return p?num(msg(p,5),1):0;}
function receive(signal,params={}){event={signal,params};sent=[];let id=entries[signal],steps=0;
 while(id){assert(++steps<5000,'execution cycle');const n=nodes.get(id),type=num(msg(n,2),5),d=defs.get(type);
  if(d?.kind==='监听信号'){id=next(n);continue;}
  if(d?.kind==='发送客户端脚本信号'){const vals={};for(const f of all(d.data,102)){const p=decode(f.v);vals[str(p,1)]=data(n,3,num(msg(p,3),2));}sent.push({signal:d.signal,target:vals['目标玩家'],params:Object.fromEntries(Object.entries(vals).filter(([k])=>k!=='目标玩家'))});id=next(n);continue;}
  if(type===22){assert.equal(data(n,3,0),'controller');state[data(n,3,1)]=data(n,3,2);id=next(n);continue;}
  if(type===323){state[data(n,3,0)]=data(n,3,1);id=next(n);continue;}
  if(type===77){settlements++;id=next(n);continue;}
  if(type===2){id=next(n,data(n,3,0)?0:1);continue;}throw Error('unsupported exec '+type);
 }
 return structuredClone(sent);
}

const checks=[];
let x=receive('GFV2Hello');
assert.deepEqual(x.map(o=>[o.signal,o.target,o.params.Slot]),[['GFV2Seat',301,1],['GFV2Seat',502,2]]);
checks.push('Hello uses both players and seats 1/2');
const payload='GFV2:-7201,123,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0';
const packet={Slot:1,Sequence:4,Ack:2,Payload:payload,Epoch:1};
x=receive('GFV2Frames',packet);assert.equal(x.length,1);assert.equal(x[0].signal,'GFV2FramesOut');assert.equal(x[0].target,502);assert.deepEqual(x[0].params,packet);
x=receive('GFV2Frames',{...packet,Slot:2});assert.equal(x.length,1);assert.equal(x[0].target,301);assert.equal(x[0].params.Payload,payload);
checks.push('Both directions preserve all five fields and the exact string');
assert.equal(receive('GFV2Frames',{...packet,Slot:3}).length,0);
assert.equal(receive('GFV2Frames',{...packet,Epoch:2}).length,0);
checks.push('Invalid slot and epoch reject');
players.splice(1);x=receive('GFV2Hello');assert.equal(x.length,1);assert.equal(x[0].params.Slot,1);
assert.equal(receive('GFV2Frames',packet).length,0);
checks.push('One-player seat and absent second-player guard');
const report={checks,nodes:nodes.size,sha256:crypto.createHash('sha256').update(b).digest('hex'),nativeImportVerified:false};
fs.writeFileSync(out+'/gfv2-native-verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
