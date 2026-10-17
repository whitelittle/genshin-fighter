import{readFileSync,writeFileSync}from'node:fs';import assert from'node:assert/strict';import{decode,encode,msg,num,str,all,get,replace,number as N,bytes as B,message as M}from'../../work/node-gia-wire.mjs';
const out="outputs/native-port-fix-20261013";const b=readFileSync("outputs/network-current-gia/gpt_20261004_165104_19角色完整联机节点.gia");const root=decode(b.subarray(20,-4));const parsed=[{b,root,graph:msg(msg(msg(msg(root,1),13),1),1)}];const originals=all(parsed[0].graph,3).map(x=>decode(x.v));
const definitions=new Map(JSON.parse(readFileSync(out+'/signal-wires.json')).map(([id,base64])=>[id,decode(Buffer.from(base64,'base64'))]));const catalog=[];
for(const[id,a]of definitions){const d=msg(msg(msg(a,14),1),1),s=msg(d,107);let signal='';for(const k of[101,102,108])signal||=str(msg(s,k),1);catalog.push({id,signal,kind:str(a,3),definition:a,data:d});}
const clone=a=>decode(encode(a)),port=(kind,index=0)=>[N(1,kind),...(index?[N(2,index)]:[])];
const pin=(kind,index=0)=>[M(1,port(kind,index)),M(2,port(kind,index))];
const pkey=p=>{const a=msg(p,1);return num(a,1)+':'+num(a,2);};
const pins=n=>all(n.wire,4).map(x=>decode(x.v));
const findPin=(wire,kind,index=0)=>all(wire,4).map(x=>decode(x.v)).find(p=>pkey(p)===kind+':'+index);
const nodes=[],byId=new Map(),edges=[],entries={},used=new Set();let nextId=1,currentLane=0,laneCounter=0;
function make(name,wire,operation){const template=clone(wire);wire=replace(clone(wire),1,[N(1,nextId)]);wire=wire.filter(f=>![4,5,6].includes(f.f));for(const p of all(template,4).map(x=>decode(x.v)))if(num(msg(p,1),1)===4)wire.push(M(4,p.filter(f=>f.f!==5)));laneCounter++;const n={id:nextId++,name,wire,template,operation,lane:currentLane};nodes.push(n);byId.set(n.id,n);return n;}
function setPin(n,kind,index,p){const key=kind+':'+index;const other=pins(n).filter(x=>pkey(x)!==key);n.wire=replace(n.wire,4,[...other.map(x=>M(4,x)),M(4,p)]);}
function literal(template,value,type){let v=clone(template);if(type==='string'){v=replace(v,105,[M(105,[B(1,String(value))])]);}else{const val=M(102,value===0?[]:[N(1,value)]);if(get(v,110)){const wrapper=msg(v,110),inner=msg(wrapper,2);let child=replace(replace(inner,102,[val]),2,[N(2,1)]);v=replace(v,110,[M(110,replace(wrapper,2,[M(2,child)]))]);}else v=replace(replace(v,102,[val]),2,[N(2,1)]);}return v;}
const intIn=originals.flatMap(n=>all(n,4).map(x=>decode(x.v))).find(p=>num(msg(p,1),1)===3&&get(p,3)&&get(msg(p,3),102));
assert(intIn,'Integer comparison sample missing');const intTemplate=msg(intIn,3);
function constant(n,kind,index,value,type='int'){const p=pin(kind,index),sample=findPin(n.template,kind,index);const template=sample&&get(sample,3)?msg(sample,3):intTemplate;p.push(M(3,literal(template,value,type)),N(4,type==='string'?6:3));setPin(n,kind,index,p);}
function linkInput(n,kind,index,source,srcKind=4,srcIndex=0,type=3,pinId){const p=pin(kind,index),sample=findPin(n.template,kind,index);if(sample&&get(sample,3))p.push(get(sample,3));p.push(N(4,type),M(5,[N(1,source.id),M(2,port(srcKind,srcIndex)),M(3,port(srcKind,srcIndex))]));if(pinId)p.push(N(7,pinId));setPin(n,kind,index,p);edges.push({from:source.id,fromKind:srcKind,fromIndex:srcIndex,to:n.id,toKind:kind,toIndex:index});}
function exec(a,b,branch=0){const p=pin(2,branch);p.push(M(5,[N(1,b.id),M(2,port(1)),M(3,port(1))]));if(a.custom){const d=all(a.custom.data,101).map(x=>decode(x.v)).find(x=>num(msg(x,3),2)===branch);if(d)p.push(N(7,num(d,8)));}setPin(a,2,branch,p);edges.push({from:a.id,fromKind:2,fromIndex:branch,to:b.id,toKind:1,toIndex:0});return b;}
function builtin(type,special=type){const t=originals.find(n=>num(msg(n,2),5)===type&&num(msg(n,3),5)===special);assert(t,'Missing builtin template '+type+'/'+special);return t;}
const self=make('获取控制实体自身',builtin(73),{kind:'self'});
function retype(wire,generic,concrete){return replace(replace(wire,2,[M(2,replace(msg(wire,2),5,[N(5,generic)]))]),3,[M(3,replace(msg(wire,3),5,[N(5,concrete)]))]);}
function baseValue(type,value){const cls=type===1?1:type===4?6:2,field=100+cls;return[N(1,cls),N(2,1),M(4,[N(1,1),M(100,[N(1,type)])]),M(field,value?[N(1,value)]:[])];}
function reflectedPin(kind,index,type,selection,value){const p=pin(kind,index);let inner=baseValue(type,value||0);if(value===undefined)inner=inner.filter(f=>f.f!==2);p.push(M(3,[N(1,10000),N(2,1),M(110,[...(selection?[N(1,selection)]:[]),M(2,inner)])]),N(4,type));return p;}
function boolInput(n,index,value){const p=pin(3,index);p.push(M(3,baseValue(4,value?1:0)),N(4,4));setPin(n,3,index,p);}
function namedInput(n,template,index,name){const p=pin(3,index);p.push(M(3,[N(1,5),N(2,1),M(4,[N(1,1),M(100,[N(1,6)])]),M(105,[B(1,name)])]),N(4,6));setPin(n,3,index,p);}
function getter(name,type='int'){const template=builtin(50,type==='entity'?52:50);const n=make('读取节点图变量 '+name,retype(template,337,type==='entity'?337:339),{kind:'getGraph',variable:name,valueType:type});namedInput(n,template,0,name);setPin(n,4,0,reflectedPin(4,0,type==='entity'?1:3,type==='entity'?0:2));return{node:n,kind:4,index:0,type:type==='entity'?1:3};}
const getters=new Map();function value(name,type='int'){const key=type+':'+name;if(!getters.has(key))getters.set(key,getter(name,type));return getters.get(key);}
const input=(n,key,source)=>{if(typeof source==='number')constant(n,3,key,source);else if(typeof source==='string')constant(n,3,key,source,'string');else linkInput(n,3,key,source.node,source.kind,source.index,source.type);};
function setter(name,v,type='int'){const template=builtin(22,type==='entity'?24:22);const n=make('设置节点图变量 '+name,retype(template,323,type==='entity'?328:323),{kind:'setGraph',variable:name,valueType:type});n.template=n.template.filter(f=>f.f!==4);namedInput(n,template,0,name);const p=reflectedPin(3,1,type==='entity'?1:3,type==='entity'?5:0,typeof v==='number'?v:undefined);if(typeof v!=='number')p.push(M(5,[N(1,v.node.id),M(2,port(v.kind,v.index)),M(3,port(v.kind,v.index))]));setPin(n,3,1,p);boolInput(n,2,false);return n;}
function compare(op,left,right){const type=op==='eq'?14:op==='gt'?232:233,special=op==='eq'?370:type,n=make(op==='eq'?'整数相等':op==='gt'?'数值大于':'数值大于等于',builtin(type,special),{kind:'compare',operator:op});input(n,0,left);input(n,1,right);return{node:n,kind:4,index:0,type:4};}
function branch(cond,yes,no){const n=make('双分支',builtin(2),{kind:'branch'});input(n,0,cond);if(yes)exec(n,yes);if(no)exec(n,no,1);return n;}
function gate(cond,pass,truth=true){return truth?branch(cond,pass):branch(cond,null,pass);}
function checks(rules,tail){for(let i=rules.length-1;i>=0;i--){const[op,left,right,truth=true]=rules[i];tail=gate(compare(op,left,right),tail,truth);}return tail;}
function appendExec(head,tail,seen=new Set()){
 if(!head||!tail||seen.has(head.id))return;seen.add(head.id);
 const type=num(msg(head.wire,2),5);const branches=type===2?[0,1]:[0];
 for(const i of branches){const p=findPin(head.wire,2,i);const target=p&&num(msg(p,5),1);
  if(target)appendExec(byId.get(target),tail,seen);else exec(head,tail,i);
 }
}
function chain(seq,tail){for(let i=seq.length-1;i>=0;i--){if(tail)appendExec(seq[i],tail);tail=seq[i];}return tail;}
function custom(signal,kind){const d=catalog.find(x=>x.signal===signal&&x.kind===kind);assert(d,'Missing '+kind+':'+signal);const template=originals.find(n=>num(msg(n,2),5)===d.id);let wire=template;if(!wire){const meta=msg(d.data,4);wire=[N(1,0),M(2,msg(meta,1)),M(3,msg(meta,2)),N(9,1)];}const n=make(kind+' '+signal,wire,{kind:kind==='监听信号'?'listen':'send',signal});n.custom=d;used.add(d.id);const sig=all(d.data,106).map(x=>decode(x.v))[0];if(sig){const p=pin(5);p.push(M(3,msg(msg(sig,4),2)),M(6,msg(sig,5)),N(7,num(sig,8)));setPin(n,5,0,p);}return n;}
function received(n){return Object.fromEntries(all(n.custom.data,103).map(x=>{const p=decode(x.v),a=msg(p,3);return[str(p,1),{node:n,kind:num(a,1),index:num(a,2),type:num(msg(p,4),4)||1}];}));}
function send(signal,target,params){const n=custom(signal,'发送客户端脚本信号');for(const f of all(n.custom.data,102)){const p=decode(f.v),key=str(p,1),a=msg(p,3),index=num(a,2);const v=key==='目标玩家'?(typeof target==='string'?value(target,'entity'):target):params[key];assert(v!==undefined,'Missing input '+signal+'.'+key);if(typeof v==='number'){constant(n,3,index,v);const pinValue=findPin(n.wire,3,index);pinValue.push(N(7,num(p,8)));setPin(n,3,index,pinValue);}else linkInput(n,3,index,v.node,v.kind,v.index,v.type,num(p,8));}return n;}
const broadcast=(signal,params)=>chain([send(signal,'P1',params),send(signal,'P2',params)]);
function lane(i){currentLane=i;laneCounter=0;}

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
const title="gpt_20261013_GF3车轮战_端口修正版",filename=title+'.gia',graphId=1073741955;
let main=clone(parsed[0].graph);main=replace(main,2,[B(2,title)]);let identity=msg(main,1);identity=replace(identity,5,[N(5,graphId)]);main=replace(main,1,[M(1,identity)]);main=replace(main,3,nodes.map(n=>M(3,n.wire)));
main=replace(main,6,[...getters.keys()].map(k=>{const at=k.indexOf(':'),type=k.slice(0,at)==='entity'?1:3,name=k.slice(at+1),initial=name.endsWith('Revision')?-1:0;return M(6,[B(2,name),N(3,type),M(4,baseValue(type,initial)),N(7,6),N(8,6)]);}));
let unit=msg(root,1);unit=replace(unit,1,[M(1,replace(msg(unit,1),4,[N(4,graphId)]))]);unit=replace(unit,3,[B(3,title)]);unit=replace(unit,2,[...used].map(id=>M(2,[N(2,23),N(4,id)])));
let wrap=msg(unit,13),inner=msg(wrap,1);inner=replace(inner,1,[M(1,main)]);wrap=replace(wrap,1,[M(1,inner)]);unit=replace(unit,13,[M(13,wrap)]);
let output=replace(root,1,[M(1,unit)]);output=replace(output,2,[...definitions.values()].map(d=>M(2,d)));output=replace(output,3,[B(3,filename)]);
const payload=encode(output),head=Buffer.from(b.subarray(0,20)),tail=b.subarray(-4);head.writeUInt32BE(payload.length+20,0);head.writeUInt32BE(payload.length,16);const result=Buffer.concat([head,payload,tail]);assert(encode(decode(result.subarray(20,-4))).equals(payload));
writeFileSync(out+'/'+filename,result);
writeFileSync(out+'/native-node-logic.json',JSON.stringify({graphId,title,filename,entries,nodes:nodes.map(n=>({id:n.id,name:n.name,operation:n.operation})),edges,signals:catalog.map(d=>({id:d.id,signal:d.signal,kind:d.kind,ports:all(d.data,d.kind==='监听信号'?103:102).map(x=>{const p=decode(x.v);return{name:str(p,1),kind:num(msg(p,3),1),index:num(msg(p,3),2),type:num(msg(p,4),4)};})})),variables:[...getters.keys()].map(k=>k.split(':').slice(1).join(':')),officialImportVerified:false},null,2));
console.log(JSON.stringify({filename,nodes:nodes.length,signals:definitions.size,wireRoundTrip:true}));
