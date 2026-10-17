import fs from 'node:fs';import assert from 'node:assert/strict';import crypto from 'node:crypto';
import{decode,encode,msg,num,str,all,get}from'../../work/node-gia-wire.mjs';
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
const checks=[];let x=receive('GF3Hello');assert.deepEqual(x.filter(x=>x.signal==='GF3Seat').map(x=>[x.target,x.params.Slot,x.params.Epoch]),[[301,1,1],[502,2,1]]);checks.push('Hello assigns both entities/seats and initial epoch');
const team=(Slot,Revision,Ready,roles,Epoch=1)=>({Slot,Epoch,Revision,Role1:roles[0]||0,Role2:roles[1]||0,Role3:roles[2]||0,Ready});
x=receive('GF3Team',team(1,0,0,[1,3]));assert(x.every(o=>o.signal==='GF3Progress'&&!('Role1'in o.params)));assert.equal(state.GF3_P1Role2,3);checks.push('Blind partial team/count only');
assert.equal(receive('GF3Team',team(2,0,1,[2,2,6])).length,0);assert.equal(receive('GF3Team',team(2,0,1,[2,0,6])).length,0);checks.push('Repeated/gapped/incomplete roles rejected');
x=receive('GF3Team',team(1,1,1,[1,3,5]));assert(!x.some(o=>o.signal==='GF3Reveal'));
x=receive('GF3Team',team(2,0,1,[2,4,6]));const reveals=x.filter(o=>o.signal==='GF3Reveal');assert.equal(reveals.length,2);assert.equal(reveals[0].params.P2Role3,6);checks.push('Both ready reveals fixed three-person order');
assert.equal(receive('GF3Team',team(1,1,1,[4,3,5])).length,0);assert.equal(receive('GF3Team',team(1,0,0,[1])).length,0);assert(receive('GF3Hello').some(o=>o.signal==='GF3Reveal'));checks.push('Locked mutation/stale revision reject; reveal retry');
receive('GF3BattleHello');x=receive('GF3BattleFrames',{Slot:1,Seq:9,Mask:0,Payload:'GF3Battle:-7201,raw',Epoch:1});assert.equal(x.length,1);assert.equal(x[0].target,502);assert.equal(x[0].params.Payload,'GF3Battle:-7201,raw');checks.push('Independent battle transport preserves raw frame string');
x=receive('GF3Reset',{Slot:1,Epoch:1,NewEpoch:2});assert.equal(state.GF3_Epoch,2);assert.equal(state.GF3_P1Revision,-1);assert.equal(state.GF3_P2Role3,0);assert(x.some(o=>o.signal==='GF3Seat'&&o.params.Epoch===2));
assert.equal(receive('GF3Team',team(2,1,1,[2,4,6])).length,0);assert.equal(receive('GF3BattleFrames',{Slot:2,Seq:10,Mask:0,Payload:'old',Epoch:1}).length,0);checks.push('Reset clears both teams and isolates old epoch/battle frames');
assert(!Object.keys(entries).some(n=>n.startsWith('GFV2')));assert(Object.keys(state).every(n=>n.startsWith('GF3_')));checks.push('No GFV2 listener or state namespace');
if(entries.GF3Quit){
 assert.equal(all(graph,6).length,17);assert(![...nodes.values()].some(n=>[22,50].includes(num(msg(n,2),5))),'must not require entity custom variables');
 x=receive('GF3Quit');assert.equal(settlements,1);assert.deepEqual(x.map(o=>[o.signal,o.target]),[['GF3Close',301],['GF3Close',502]]);
 receive('GF3Quit');assert.equal(settlements,1,'exit retries must not settle twice');checks.push('17 embedded graph variables; close both clients; settle once even on retries');
}
const report={checks,wireRoundTrip:true,nodes:nodes.size,sha256:crypto.createHash('sha256').update(b).digest('hex'),nativeImportVerified:false};fs.writeFileSync(out+'/native-node-verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
