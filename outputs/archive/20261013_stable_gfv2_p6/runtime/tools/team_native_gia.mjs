// Build an independent native GF3 graph using verified exported node/port templates.
import fs from 'node:fs';import assert from 'node:assert/strict';import crypto from 'node:crypto';import{pathToFileURL}from'node:url';
import{execFileSync}from'node:child_process';import path from'node:path';
import{decode,encode,msg,num,str,all,replace,number as N,bytes as B,message as M}from'../../work/node-gia-wire.mjs';
const out=process.argv.includes('--out')?process.argv[process.argv.indexOf('--out')+1]:'outputs/team-battle-20261013';fs.mkdirSync(out,{recursive:true});
const source='outputs/network-current-gia/gpt_20261004_165104_19角色完整联机节点.gia';
const b=fs.readFileSync(source),root=decode(b.subarray(20,-4));assert(encode(root).equals(b.subarray(20,-4)));
const originalDefs=all(root,2).map(x=>decode(x.v));
function info(def){const data=msg(msg(msg(def,14),1),1),sig=msg(data,107);let signal='';for(const f of[101,102,108])signal||=str(msg(sig,f),1);return{definition:def,data,signal,kind:str(def,3),id:num(msg(def,1),4)};}
const originals=originalDefs.map(info),newDefs=[];let nextDef=1610620000;
const specs=[
 ['GF3Hello','FighterHello',[]],['GF3Seat','FighterTeam',['Slot','Epoch']],
 ['GF3Team','FighterTeam',['Slot','Epoch','Revision','Role1','Role2','Role3','Ready']],
 ['GF3Progress','FighterTeam',['Epoch','Slot','Count','Ready','Revision']],
 ['GF3Reveal','FighterTeam',['Epoch','Revision1','Revision2','P1Role1','P1Role2','P1Role3','P2Role1','P2Role2','P2Role3']],
 ['GF3Reset','FighterTeam',['Slot','Epoch','NewEpoch']],
 ['GF3BattleHello','FighterHello',[]],['GF3BattleSeat','FighterSeat',['Slot']],
 ['GF3BattleFrames','FighterFrames',['Slot','Seq','Mask','Payload','Epoch']],
 ['GF3BattleFramesOut','FighterFramesOut',['Slot','Seq','Mask','Payload','Epoch']],
 ['GF3Quit','FighterHello',[]],['GF3Close','FighterHello',[]]
];
function remap(fields,ids,oldName,newName){return fields.map(f=>{
 if(f.w===0&&ids.has(Number(f.v)))return N(f.f,ids.get(Number(f.v)));
 if(f.w!==2)return f;if(f.v.toString('utf8')===oldName)return B(f.f,newName);
 try{const nested=decode(f.v);return M(f.f,remap(nested,ids,oldName,newName));}catch{return f;}
});}
for(const[name,base,params]of specs){
 const family=originals.filter(d=>d.signal===base);assert(family.length===4,base);
 const ids=new Map(family.map(d=>[d.id,nextDef++]));
 for(const old of family){
  let def=remap(old.definition,ids,base,name),d=msg(msg(msg(def,14),1),1);
  for(const field of[102,103]){
   const ports=all(d,field).map(x=>decode(x.v));if(!ports.length)continue;
   const dataPorts=ports.filter(p=>!['事件源实体','事件源GUID','信号来源实体','目标玩家'].includes(str(p,1)));
   assert(dataPorts.length>=params.length,[name,old.kind]);
   const keep=ports.filter(p=>!dataPorts.includes(p));
   dataPorts.slice(0,params.length).forEach((p,i)=>keep.push(replace(p,1,[B(1,params[i])])));
   d=replace(d,field,keep.map(p=>M(field,p)));
  }
  let a=msg(def,14),c=msg(a,1);c=replace(c,1,[M(1,d)]);a=replace(a,1,[M(1,c)]);def=replace(def,14,[M(14,a)]);
  newDefs.push(def);
 }
}
// Reuse the already verified wire builder, not guessed builtin IDs or pins.
const oldBuilder=fs.readFileSync('work/build-official-network-gia.mjs','utf8');
let helpers=oldBuilder.slice(oldBuilder.indexOf('const clone='),oldBuilder.indexOf('// Hello uses'));
helpers=helpers.replace("wire=wire.filter(f=>![4,5,6].includes(f.f));laneCounter++", "wire=wire.filter(f=>![4,5,6].includes(f.f));for(const p of all(template,4).map(x=>decode(x.v)))if(num(msg(p,1),1)===4)wire.push(M(4,p.filter(f=>f.f!==5)));laneCounter++");
helpers=helpers.replace(/const intIn=[^\n]+;/,"const intIn=originals.flatMap(n=>all(n,4).map(x=>decode(x.v))).find(p=>num(msg(p,1),1)===3&&get(p,3)&&get(msg(p,3),102));");
helpers=helpers.replace(/function chain\(seq,tail\)\{[^\n]+\}/,`function appendExec(head,tail,seen=new Set()){
 if(!head||!tail||seen.has(head.id))return;seen.add(head.id);
 const type=num(msg(head.wire,2),5);const branches=type===2?[0,1]:[0];
 for(const i of branches){const p=findPin(head.wire,2,i);const target=p&&num(msg(p,5),1);
  if(target)appendExec(byId.get(target),tail,seen);else exec(head,tail,i);
 }
}
function chain(seq,tail){for(let i=seq.length-1;i>=0;i--){if(tail)appendExec(seq[i],tail);tail=seq[i];}return tail;}`);
// Real node IDs/ports from the public Genshin-TS vendor catalog and gia.proto.
// Embedded graph variables remove the old manual entity-variable prerequisite.
helpers=helpers.replace(/function getter\(name,type='int'\)\{[\s\S]*?\}\nconst getters=/,`function retype(wire,generic,concrete){return replace(replace(wire,2,[M(2,replace(msg(wire,2),5,[N(5,generic)]))]),3,[M(3,replace(msg(wire,3),5,[N(5,concrete)]))]);}
function baseValue(type,value){const cls=type===1?1:type===4?6:2,field=100+cls;return[N(1,cls),N(2,1),M(4,[N(1,1),M(100,[N(1,type)])]),M(field,value?[N(1,value)]:[])];}
function reflectedPin(kind,index,type,selection,value){const p=pin(kind,index);let inner=baseValue(type,value||0);if(value===undefined)inner=inner.filter(f=>f.f!==2);p.push(M(3,[N(1,10000),N(2,1),M(110,[...(selection?[N(1,selection)]:[]),M(2,inner)])]),N(4,type));return p;}
function boolInput(n,index,value){const p=pin(3,index);p.push(M(3,baseValue(4,value?1:0)),N(4,4));setPin(n,3,index,p);}
function namedInput(n,template,index,name){const p=pin(3,index);p.push(M(3,[N(1,5),N(2,1),M(4,[N(1,1),M(100,[N(1,6)])]),M(105,[B(1,name)])]),N(4,6));setPin(n,3,index,p);}
function getter(name,type='int'){const template=builtin(50,type==='entity'?52:50);const n=make('读取节点图变量 '+name,retype(template,337,type==='entity'?337:339),{kind:'getGraph',variable:name,valueType:type});namedInput(n,template,0,name);setPin(n,4,0,reflectedPin(4,0,type==='entity'?1:3,type==='entity'?0:2));return{node:n,kind:4,index:0,type:type==='entity'?1:3};}
const getters=`);
helpers=helpers.replace(/^function setter\(name,v,type='int'\)\{[^\n]+\}/m,`function setter(name,v,type='int'){const template=builtin(22,type==='entity'?24:22);const n=make('设置节点图变量 '+name,retype(template,323,type==='entity'?328:323),{kind:'setGraph',variable:name,valueType:type});n.template=n.template.filter(f=>f.f!==4);namedInput(n,template,0,name);const p=reflectedPin(3,1,type==='entity'?1:3,type==='entity'?5:0,typeof v==='number'?v:undefined);if(typeof v!=='number')p.push(M(5,[N(1,v.node.id),M(2,port(v.kind,v.index)),M(3,port(v.kind,v.index))]));setPin(n,3,1,p);boolInput(n,2,false);return n;}`);
const header=`import{readFileSync,writeFileSync}from'node:fs';import assert from'node:assert/strict';import{decode,encode,msg,num,str,all,get,replace,number as N,bytes as B,message as M}from'../../work/node-gia-wire.mjs';
const out=${JSON.stringify(out)};const b=readFileSync(${JSON.stringify(source)});const root=decode(b.subarray(20,-4));const parsed=[{b,root,graph:msg(msg(msg(msg(root,1),13),1),1)}];const originals=all(parsed[0].graph,3).map(x=>decode(x.v));
const definitions=new Map(JSON.parse(readFileSync(out+'/signal-wires.json')).map(([id,base64])=>[id,decode(Buffer.from(base64,'base64'))]));const catalog=[];
for(const[id,a]of definitions){const d=msg(msg(msg(a,14),1),1),s=msg(d,107);let signal='';for(const k of[101,102,108])signal||=str(msg(s,k),1);catalog.push({id,signal,kind:str(a,3),definition:a,data:d});}
`;
const logic=`
const players=make('获取在场玩家实体列表',builtin(248),{kind:'players'}),length=make('获取列表长度',builtin(142,144),{kind:'length'});linkInput(length,3,0,players,4,0,13);
function at(index){const n=make('玩家'+index,builtin(128,130),{kind:'index'});linkInput(n,3,0,players,4,0,13);input(n,1,index);return{node:n,kind:4,index:0,type:1};}
const p1=at(0),p2=at(1),len={node:length,kind:4,index:0,type:3};
function both(signal,params){const second=gate(compare('ge',len,2),send(signal,'GF3_P2',params));return chain([send(signal,'GF3_P1',params)],second);}
function progressSide(side){const prefix='GF3_P'+side;const params={Epoch:value('GF3_Epoch'),Slot:side,Ready:value(prefix+'Ready'),Revision:value(prefix+'Revision')};
 const count=n=>both('GF3Progress',{...params,Count:n});return branch(compare('gt',value(prefix+'Role3'),0),count(3),branch(compare('gt',value(prefix+'Role2'),0),count(2),branch(compare('gt',value(prefix+'Role1'),0),count(1),count(0))));}
function progress(){return chain([progressSide(1),progressSide(2)]);}
function reveal(){const params={Epoch:value('GF3_Epoch'),Revision1:value('GF3_P1Revision'),Revision2:value('GF3_P2Revision')};for(let side=1;side<=2;side++)for(let n=1;n<=3;n++)params['P'+side+'Role'+n]=value('GF3_P'+side+'Role'+n);
 return gate(compare('eq',value('GF3_P1Ready'),1),gate(compare('eq',value('GF3_P2Ready'),1),chain([setter('GF3_Locked',1)],both('GF3Reveal',params))));}
function report(){return chain([progress()],reveal());}
function seats(){return chain([send('GF3Seat','GF3_P1',{Slot:1,Epoch:value('GF3_Epoch')})],gate(compare('ge',len,2),send('GF3Seat','GF3_P2',{Slot:2,Epoch:value('GF3_Epoch')})));}
function reset(next){const seq=[setter('GF3_Epoch',next),setter('GF3_Locked',0)];for(let side=1;side<=2;side++){const p='GF3_P'+side;seq.push(setter(p+'Ready',0),setter(p+'Revision',-1));for(let n=1;n<=3;n++)seq.push(setter(p+'Role'+n,0));}return chain(seq);}
lane(0);const hello=custom('GF3Hello','监听信号');entries.GF3Hello=hello.id;
const helloOut=chain([seats()],report());const init=chain([reset(1)],helloOut);
const epoch=branch(compare('gt',value('GF3_Epoch'),0),helloOut,init);
const helloSave=chain([setter('GF3_P1',p1,'entity')],chain([gate(compare('ge',len,2),setter('GF3_P2',p2,'entity'))],epoch));
exec(hello,gate(compare('ge',len,1),helloSave));
lane(1);const team=custom('GF3Team','监听信号'),t=received(team);entries.GF3Team=team.id;
function saveTeam(side){const p='GF3_P'+side;const save=chain(['Role1','Role2','Role3','Ready','Revision'].map(k=>setter(p+k,t[k])),report());
 const exact=checks([['eq',t.Revision,value(p+'Revision')],['eq',t.Ready,value(p+'Ready')],...['Role1','Role2','Role3'].map(k=>['eq',t[k],value(p+k)])],report());
 return branch(compare('eq',value('GF3_Locked'),1),exact,branch(compare('eq',t.Revision,value(p+'Revision')),exact,checks([['gt',t.Revision,value(p+'Revision')]],save)));}
const choose=branch(compare('eq',t.Slot,1),saveTeam(1),saveTeam(2));
const distinct=checks([['eq',t.Role1,t.Role2,false],['eq',t.Role1,t.Role3,false],['eq',t.Role2,t.Role3,false]],choose);
const partial=branch(compare('gt',t.Role3,0),checks([['gt',t.Role1,0],['gt',t.Role2,0]],distinct),branch(compare('gt',t.Role2,0),checks([['gt',t.Role1,0],['eq',t.Role1,t.Role2,false]],choose),choose));
const complete=checks([['gt',t.Role1,0],['gt',t.Role2,0],['gt',t.Role3,0]],distinct);
const rules=[['ge',len,t.Slot],['ge',t.Slot,1],['ge',2,t.Slot],['eq',t.Epoch,value('GF3_Epoch')],['ge',t.Revision,0],['ge',t.Ready,0],['ge',1,t.Ready],...['Role1','Role2','Role3'].flatMap(k=>[['ge',t[k],0],['ge',6,t[k]]])];
exec(team,checks(rules,branch(compare('eq',t.Ready,1),complete,partial)));
lane(2);const resetListener=custom('GF3Reset','监听信号'),r=received(resetListener);entries.GF3Reset=resetListener.id;
const resetNow=chain([reset(r.NewEpoch),seats()],progress());
exec(resetListener,checks([['ge',r.Slot,1],['ge',2,r.Slot],['ge',len,r.Slot],['eq',r.Epoch,value('GF3_Epoch')],['gt',r.NewEpoch,r.Epoch]],resetNow));
lane(3);const battleHello=custom('GF3BattleHello','监听信号');entries.GF3BattleHello=battleHello.id;
const second=chain([setter('GF3_BattleP2',p2,'entity'),send('GF3BattleSeat',p2,{Slot:2})]);
const first=chain([setter('GF3_BattleP1',p1,'entity'),send('GF3BattleSeat',p1,{Slot:1})],gate(compare('ge',len,2),second));exec(battleHello,gate(compare('ge',len,1),first));
lane(4);const frames=custom('GF3BattleFrames','监听信号'),f=received(frames);entries.GF3BattleFrames=frames.id;
const route=branch(compare('eq',f.Slot,1),send('GF3BattleFramesOut','GF3_BattleP2',f),send('GF3BattleFramesOut','GF3_BattleP1',f));
exec(frames,checks([['ge',len,2],['ge',f.Slot,1],['ge',2,f.Slot],['eq',f.Epoch,value('GF3_Epoch')]],route));
lane(5);const quit=custom('GF3Quit','监听信号');entries.GF3Quit=quit.id;
const close=()=>chain([send('GF3Close',p1,{})],gate(compare('ge',len,2),send('GF3Close',p2,{})));
const settle=make('结算关卡（主动退出）',retype(builtin(2),77,77),{kind:'settle'});boolInput(settle,0,false);
exec(quit,gate(compare('ge',len,1),branch(compare('eq',value('GF3_QuitDone'),0),chain([setter('GF3_QuitDone',1),close()],settle),close())));
let y=0;for(let l=0;l<5;l++){const a=nodes.filter(n=>n.lane===l);a.forEach((n,i)=>{for(const[field,v]of[[5,160+i%7*460],[6,y+Math.floor(i/7)*880]]){const x=Buffer.alloc(4);x.writeFloatLE(v);n.wire.push({f:field,w:5,v:x});}});y+=Math.ceil(a.length/7)*880+1000;}
const title=${JSON.stringify(process.argv.includes('--name')?process.argv[process.argv.indexOf('--name')+1]:'gpt_20261013_GF3车轮战_自带变量_结算关闭')},filename=title+'.gia',graphId=1073741955;
let main=clone(parsed[0].graph);main=replace(main,2,[B(2,title)]);let identity=msg(main,1);identity=replace(identity,5,[N(5,graphId)]);main=replace(main,1,[M(1,identity)]);main=replace(main,3,nodes.map(n=>M(3,n.wire)));
main=replace(main,6,[...getters.keys()].map(k=>{const at=k.indexOf(':'),type=k.slice(0,at)==='entity'?1:3,name=k.slice(at+1),initial=name.endsWith('Revision')?-1:0;return M(6,[B(2,name),N(3,type),M(4,baseValue(type,initial)),N(7,6),N(8,6)]);}));
let unit=msg(root,1);unit=replace(unit,1,[M(1,replace(msg(unit,1),4,[N(4,graphId)]))]);unit=replace(unit,3,[B(3,title)]);unit=replace(unit,2,[...used].map(id=>M(2,[N(2,23),N(4,id)])));
let wrap=msg(unit,13),inner=msg(wrap,1);inner=replace(inner,1,[M(1,main)]);wrap=replace(wrap,1,[M(1,inner)]);unit=replace(unit,13,[M(13,wrap)]);
let output=replace(root,1,[M(1,unit)]);output=replace(output,2,[...definitions.values()].map(d=>M(2,d)));output=replace(output,3,[B(3,filename)]);
const payload=encode(output),head=Buffer.from(b.subarray(0,20)),tail=b.subarray(-4);head.writeUInt32BE(payload.length+20,0);head.writeUInt32BE(payload.length,16);const result=Buffer.concat([head,payload,tail]);assert(encode(decode(result.subarray(20,-4))).equals(payload));
writeFileSync(out+'/'+filename,result);
writeFileSync(out+'/native-node-logic.json',JSON.stringify({graphId,title,filename,entries,nodes:nodes.map(n=>({id:n.id,name:n.name,operation:n.operation})),edges,signals:catalog.map(d=>({id:d.id,signal:d.signal,kind:d.kind,ports:all(d.data,d.kind==='监听信号'?103:102).map(x=>{const p=decode(x.v);return{name:str(p,1),kind:num(msg(p,3),1),index:num(msg(p,3),2),type:num(msg(p,4),4)};})})),variables:[...getters.keys()].map(k=>k.split(':').slice(1).join(':')),officialImportVerified:false},null,2));
console.log(JSON.stringify({filename,nodes:nodes.length,signals:definitions.size,wireRoundTrip:true}));
`;
fs.writeFileSync(out+'/signal-wires.json',JSON.stringify(newDefs.map(d=>[num(msg(d,1),4),encode(d).toString('base64')])));
const generated='runtime/tools/team_nodes_generated.mjs';fs.writeFileSync(generated,header+helpers+logic);
await import(pathToFileURL(fs.realpathSync(generated)).href);
const report=JSON.parse(fs.readFileSync(out+'/native-node-logic.json','utf8'));
execFileSync(process.execPath,[path.resolve(import.meta.dirname,'check_native_ports.mjs'),out+'/'+report.filename,'--report',out+'/port-verification.json'],{stdio:'inherit'});
