import{readFileSync,writeFileSync,mkdirSync,existsSync}from'node:fs';import{createHash}from'node:crypto';import assert from'node:assert/strict';
import{decode,encode,msg,num,str,all,get,replace,number as N,bytes as B,message as M}from'./node-gia-wire.mjs';
const out='outputs/network-current-gia';mkdirSync(out,{recursive:true});
const samples=process.argv.slice(2);if(samples.length===0)samples.push('C:/Users/Cheng/Desktop/联机节点图2.gia','C:/Users/Cheng/Desktop/联机节点图3.gia');
const parsed=samples.map(path=>{const b=readFileSync(path),p=b.subarray(20,20+b.readUInt32BE(16)),root=decode(p);assert(encode(root).equals(p));return{b,root,graph:msg(msg(msg(msg(root,1),13),1),1),hash:createHash('sha256').update(b).digest('hex'),filename:path.split(/[\\/]/).pop()};});
const originals=parsed.flatMap(p=>all(p.graph,3).map(x=>decode(x.v))),definitions=new Map();
for(const p of parsed)for(const f of all(p.root,2)){const a=decode(f.v);definitions.set(num(msg(a,1),4),a);}
const catalog=[];for(const[id,a]of definitions){const d=msg(msg(msg(a,14),1),1),s=msg(d,107);let signal='';for(const k of[101,102,108])signal ||=str(msg(s,k),1);catalog.push({id,signal,kind:str(a,3),definition:a,data:d});}
const signals=['FighterHello','FighterSeat','FighterTeam','FighterTeamOut','FighterJoin','FighterJoined','FighterFrames','FighterFramesOut','FighterFlow','FighterFlowOut'];for(const s of signals)assert(catalog.some(d=>d.signal===s),'Missing exported signal '+s);
const clone=a=>decode(encode(a)),port=(kind,index=0)=>[N(1,kind),...(index?[N(2,index)]:[])];
const pin=(kind,index=0)=>[M(1,port(kind,index)),M(2,port(kind,index))];
const pkey=p=>{const a=msg(p,1);return num(a,1)+':'+num(a,2);};
const pins=n=>all(n.wire,4).map(x=>decode(x.v));
const findPin=(wire,kind,index=0)=>all(wire,4).map(x=>decode(x.v)).find(p=>pkey(p)===kind+':'+index);
const nodes=[],byId=new Map(),edges=[],entries={},used=new Set();let nextId=1,currentLane=0,laneCounter=0;
function make(name,wire,operation){const template=clone(wire);wire=replace(clone(wire),1,[N(1,nextId)]);wire=wire.filter(f=>![4,5,6].includes(f.f));laneCounter++;const n={id:nextId++,name,wire,template,operation,lane:currentLane};nodes.push(n);byId.set(n.id,n);return n;}
function setPin(n,kind,index,p){const key=kind+':'+index;const other=pins(n).filter(x=>pkey(x)!==key);n.wire=replace(n.wire,4,[...other.map(x=>M(4,x)),M(4,p)]);}
function literal(template,value,type){let v=clone(template);if(type==='string'){v=replace(v,105,[M(105,[B(1,String(value))])]);}else{const val=M(102,value===0?[]:[N(1,value)]);if(get(v,110)){const wrapper=msg(v,110),inner=msg(wrapper,2);let child=replace(replace(inner,102,[val]),2,[N(2,1)]);v=replace(v,110,[M(110,replace(wrapper,2,[M(2,child)]))]);}else v=replace(replace(v,102,[val]),2,[N(2,1)]);}return v;}
const intIn=findPin(originals.find(n=>num(n,1)===54&&num(msg(n,2),5)===232),3,0);
assert(intIn,'Integer comparison sample missing');const intTemplate=msg(intIn,3);
function constant(n,kind,index,value,type='int'){const p=pin(kind,index),sample=findPin(n.template,kind,index);const template=sample&&get(sample,3)?msg(sample,3):intTemplate;p.push(M(3,literal(template,value,type)),N(4,type==='string'?6:3));setPin(n,kind,index,p);}
function linkInput(n,kind,index,source,srcKind=4,srcIndex=0,type=3,pinId){const p=pin(kind,index),sample=findPin(n.template,kind,index);if(sample&&get(sample,3))p.push(get(sample,3));p.push(N(4,type),M(5,[N(1,source.id),M(2,port(srcKind,srcIndex)),M(3,port(srcKind,srcIndex))]));if(pinId)p.push(N(7,pinId));setPin(n,kind,index,p);edges.push({from:source.id,fromKind:srcKind,fromIndex:srcIndex,to:n.id,toKind:kind,toIndex:index});}
function exec(a,b,branch=0){const p=pin(2,branch);p.push(M(5,[N(1,b.id),M(2,port(1)),M(3,port(1))]));if(a.custom){const d=all(a.custom.data,101).map(x=>decode(x.v)).find(x=>num(msg(x,3),2)===branch);if(d)p.push(N(7,num(d,8)));}setPin(a,2,branch,p);edges.push({from:a.id,fromKind:2,fromIndex:branch,to:b.id,toKind:1,toIndex:0});return b;}
function builtin(type,special=type){const t=originals.find(n=>num(msg(n,2),5)===type&&num(msg(n,3),5)===special);assert(t,'Missing builtin template '+type+'/'+special);return t;}
const self=make('获取控制实体自身',builtin(73),{kind:'self'});
function getter(name,type='int'){const template=builtin(50,type==='entity'?52:50),n=make('读取 '+name,template,{kind:'get',variable:name,valueType:type});linkInput(n,3,0,self,4,0,1);const np=clone(findPin(template,3,1));np.splice(0,np.length,...pin(3,1),M(3,literal(msg(findPin(template,3,1),3),name,'string')),N(4,6));setPin(n,3,1,np);
 const rp=clone(findPin(template,4,0));setPin(n,4,0,rp);return{node:n,kind:4,index:0,type:type==='entity'?1:3};}
const getters=new Map();function value(name,type='int'){const key=type+':'+name;if(!getters.has(key))getters.set(key,getter(name,type));return getters.get(key);}
const input=(n,key,source)=>{if(typeof source==='number')constant(n,3,key,source);else if(typeof source==='string')constant(n,3,key,source,'string');else linkInput(n,3,key,source.node,source.kind,source.index,source.type);};
function setter(name,v,type='int'){const template=builtin(22,type==='entity'?24:22),n=make('设置 '+name,template,{kind:'set',variable:name,valueType:type});linkInput(n,3,0,self,4,0,1);const np=pin(3,1);np.push(M(3,literal(msg(findPin(template,3,1),3),name,'string')),N(4,6));setPin(n,3,1,np);input(n,2,v);return n;}
function compare(op,left,right){const type=op==='eq'?14:op==='gt'?232:233,special=op==='eq'?370:type,n=make(op==='eq'?'整数相等':op==='gt'?'数值大于':'数值大于等于',builtin(type,special),{kind:'compare',operator:op});input(n,0,left);input(n,1,right);return{node:n,kind:4,index:0,type:4};}
function branch(cond,yes,no){const n=make('双分支',builtin(2),{kind:'branch'});input(n,0,cond);if(yes)exec(n,yes);if(no)exec(n,no,1);return n;}
function gate(cond,pass,truth=true){return truth?branch(cond,pass):branch(cond,null,pass);}
function checks(rules,tail){for(let i=rules.length-1;i>=0;i--){const[op,left,right,truth=true]=rules[i];tail=gate(compare(op,left,right),tail,truth);}return tail;}
function chain(seq,tail){for(let i=seq.length-1;i>=0;i--){if(tail)exec(seq[i],tail);tail=seq[i];}return tail;}
function custom(signal,kind){const d=catalog.find(x=>x.signal===signal&&x.kind===kind);assert(d,'Missing '+kind+':'+signal);const template=originals.find(n=>num(msg(n,2),5)===d.id);let wire=template;if(!wire){const meta=msg(d.data,4);wire=[N(1,0),M(2,msg(meta,1)),M(3,msg(meta,2)),N(9,1)];}const n=make(kind+' '+signal,wire,{kind:kind==='监听信号'?'listen':'send',signal});n.custom=d;used.add(d.id);const sig=all(d.data,106).map(x=>decode(x.v))[0];if(sig){const p=pin(5);p.push(M(3,msg(msg(sig,4),2)),M(6,msg(sig,5)),N(7,num(sig,8)));setPin(n,5,0,p);}return n;}
function received(n){return Object.fromEntries(all(n.custom.data,103).map(x=>{const p=decode(x.v),a=msg(p,3);return[str(p,1),{node:n,kind:num(a,1),index:num(a,2),type:num(msg(p,4),4)||1}];}));}
function send(signal,target,params){const n=custom(signal,'发送客户端脚本信号');for(const f of all(n.custom.data,102)){const p=decode(f.v),key=str(p,1),a=msg(p,3),index=num(a,2);const v=key==='目标玩家'?(typeof target==='string'?value(target,'entity'):target):params[key];assert(v!==undefined,'Missing input '+signal+'.'+key);if(typeof v==='number'){constant(n,3,index,v);const pinValue=findPin(n.wire,3,index);pinValue.push(N(7,num(p,8)));setPin(n,3,index,pinValue);}else linkInput(n,3,index,v.node,v.kind,v.index,v.type,num(p,8));}return n;}
const broadcast=(signal,params)=>chain([send(signal,'P1',params),send(signal,'P2',params)]);
function lane(i){currentLane=i;laneCounter=0;}
// Hello uses the exported list and index nodes; no match state is reset here.
lane(0);const hello=custom('FighterHello','监听信号');entries.FighterHello=hello.id;
const list=make('获取在场玩家实体列表',builtin(248),{kind:'players'}),length=make('获取列表长度',builtin(142,144),{kind:'length'});linkInput(length,3,0,list,4,0,13);
function at(index){const n=make('列表第'+index+'项',builtin(128,130),{kind:'index'});linkInput(n,3,0,list,4,0,13);input(n,1,index);return{node:n,kind:4,index:0,type:1};}
const player2=at(1),player1=at(0);
const seat2=chain([setter('P2',player2,'entity'),send('FighterSeat',player2,{Slot:2})]);const two=gate(compare('ge',{node:length,kind:4,index:0,type:3},2),seat2);
const seat1=chain([setter('P1',player1,'entity'),send('FighterSeat',player1,{Slot:1})],two);exec(hello,gate(compare('ge',{node:length,kind:4,index:0,type:3},1),seat1));
lane(1);const team=custom('FighterTeam','监听信号'),t=received(team);entries.FighterTeam=team.id;
const replyParams={...t,Stage:value('Stage'),Epoch:t.Epoch,Round:value('Round'),Wins1:value('Wins1'),Wins2:value('Wins2')};
const teamReply=broadcast('FighterTeamOut',replyParams);
function teamFor(slot){const p='P'+slot;
 const set=[];if(slot===1)for(const name of['Stage','Round','Wins1','Wins2'])set.push(setter(name,t[name]));
 for(const name of['Role1','Role2','Role3','Ready','Revision'])set.push(setter(p+name,t[name]));
 const save=chain(set,teamReply);return checks([['gt',value(p+'Revision'),t.Revision,false]],save);}
const slotChoice=branch(compare('eq',t.Slot,1),teamFor(1),teamFor(2));
const reset=chain([setter('P1Ready',0),setter('P2Ready',0),setter('P1Revision',-1),setter('P2Revision',-1),setter('Epoch',t.Epoch)],slotChoice);
const epochStep=branch(compare('gt',t.Epoch,value('Epoch')),reset,slotChoice);
const rolesComplete=checks([['gt',t.Role1,0],['gt',t.Role2,0],['gt',t.Role3,0],['eq',t.Role1,t.Role2,false],['eq',t.Role1,t.Role3,false],['eq',t.Role2,t.Role3,false]],epochStep);
const readyCheck=branch(compare('eq',t.Ready,1),rolesComplete,branch(compare('eq',t.Ready,2),rolesComplete,epochStep));
const validRules=[['ge',t.Slot,1],['ge',2,t.Slot],['ge',t.Ready,0],['ge',3,t.Ready],...['Role1','Role2','Role3'].flatMap(k=>[['ge',t[k],0],['ge',19,t[k]]]),['ge',t.Stage,1],['ge',210,t.Stage],['ge',t.Round,1],['ge',3,t.Round],['ge',t.Wins1,0],['ge',2,t.Wins1],['ge',t.Wins2,0],['ge',2,t.Wins2],['ge',t.Epoch,1],['ge',t.Revision,0],['gt',value('Epoch'),t.Epoch,false]];
exec(team,checks(validRules,readyCheck));
lane(2);const join=custom('FighterJoin','监听信号'),j=received(join);entries.FighterJoin=join.id;
exec(join,checks([['ge',{node:length,kind:4,index:0,type:3},2],['eq',j.Epoch,value('Epoch')],['eq',value('P1Ready'),2],['eq',value('P2Ready'),2]],broadcast('FighterJoined',{Epoch:j.Epoch})));
lane(3);const frames=custom('FighterFrames','监听信号'),f=received(frames);entries.FighterFrames=frames.id;
const route=branch(compare('eq',f.Slot,1),send('FighterFramesOut','P2',f),gate(compare('eq',f.Slot,2),send('FighterFramesOut','P1',f)));
exec(frames,checks([['eq',f.Epoch,value('Epoch')],['eq',value('P1Ready'),2],['eq',value('P2Ready'),2]],route));
lane(4);const flow=custom('FighterFlow','监听信号'),fl=received(flow);entries.FighterFlow=flow.id;
const flowReply=broadcast('FighterFlowOut',fl);
// Exit notifications may arrive before/after Team advances Epoch. The current
// client performs the +/-1 Epoch and Revision checks; do not reject them here.
const action=branch(compare('eq',fl.Action,1),gate(compare('eq',fl.Epoch,value('Epoch')),flowReply),flowReply);
exec(flow,checks([['ge',fl.Slot,1],['ge',2,fl.Slot],['ge',fl.Action,1],['ge',3,fl.Action],['ge',fl.Epoch,1],['ge',fl.Revision,0]],action));
// Reserve enough vertical space for the eleven-parameter signal nodes. Keep
// chains in separate lanes rather than overlaying the original sample graphs.
let laneY=0;for(let lane=0;lane<5;lane++){const items=nodes.filter(n=>n.lane===lane);items.forEach((n,i)=>{for(const[field,v]of[[5,160+(i%7)*460],[6,laneY+Math.floor(i/7)*880]]){const b=Buffer.alloc(4);b.writeFloatLE(v);n.wire.push({f:field,w:5,v:b});}});laneY+=Math.ceil(items.length/7)*880+1200;}
// Regenerate the graph while preserving every unrelated exported field.
const stamp=new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(new Date()).replace(/[-: ]/g,'').replace(/^(\d{8})(\d{6})$/,'$1_$2');
const title='gpt_'+stamp+'_19角色完整联机节点',filename=title+'.gia',graphId=1073741927;
let main=clone(parsed[0].graph);main=replace(main,2,[B(2,title)]);let identity=msg(main,1);identity=replace(identity,5,[N(5,graphId)]);main=replace(main,1,[M(1,identity)]);main=replace(main,3,nodes.map(n=>M(3,n.wire)));
let gunit=msg(parsed[0].root,1);gunit=replace(gunit,1,[M(1,replace(msg(gunit,1),4,[N(4,graphId)]))]);gunit=replace(gunit,3,[B(3,title)]);gunit=replace(gunit,2,[...used].map(id=>M(2,[N(2,23),N(4,id)])));
let wrap=msg(gunit,13),wrap1=msg(wrap,1);wrap1=replace(wrap1,1,[M(1,main)]);wrap=replace(wrap,1,[M(1,wrap1)]);gunit=replace(gunit,13,[M(13,wrap)]);
let root=clone(parsed[0].root);root=replace(root,1,[M(1,gunit)]);root=replace(root,2,[...definitions.values()].map(d=>M(2,d)));root=replace(root,3,[B(3,filename)]);
const payload=encode(root),header=Buffer.from(parsed[0].b.subarray(0,20)),tail=parsed[0].b.subarray(parsed[0].b.length-4);header.writeUInt32BE(payload.length+20,0);header.writeUInt32BE(payload.length,16);const result=Buffer.concat([header,payload,tail]);assert(!existsSync(out+'/'+filename));
const logic={title,filename,graphId,entries,nodes:nodes.map(n=>({id:n.id,name:n.name,operation:n.operation})),edges,variables:['P1','P2','Epoch','Stage','Round','Wins1','Wins2','P1Role1','P1Role2','P1Role3','P1Ready','P1Revision','P2Role1','P2Role2','P2Role3','P2Ready','P2Revision'],exitEpochCheck:'Client handles +/-1 Epoch and Flow Revision; server checks exact Epoch only for rematch Action=1',sourceIdentityValidation:false};
writeFileSync(out+'/'+filename,result);writeFileSync(out+'/generated-logic.json',JSON.stringify(logic,null,2));writeFileSync(out+'/delivery.json',JSON.stringify({stamp,filename,bytes:result.length,sha256:createHash('sha256').update(result).digest('hex'),graphId,nodes:nodes.length,signalDefinitions:definitions.size,sourceSamples:parsed.map(p=>({filename:p.filename,sha256:p.hash})),officialImportVerified:false},null,2));
console.log(JSON.stringify({filename,nodes:nodes.length,signalDefinitions:definitions.size,bytes:result.length,officialImportVerified:false}));
