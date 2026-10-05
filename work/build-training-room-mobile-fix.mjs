import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {exportGia,importGia,validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const base=JSON.parse(fs.readFileSync('work/full-art-return-latest.json')).out;
const save=JSON.parse(fs.readFileSync(base+'/simulator.save.json'));
const native=JSON.parse(fs.readFileSync(base+'/fighter.save.json'));
let lua=native.assets.scripts[0].source;
const dataLines=['local portraitData=','local thumbData=','resourceGate.homePortraitData=','local Collision='].map(prefix=>lua.split('\n').find(line=>line.startsWith(prefix)));
assert(dataLines.every(Boolean));
const replaceOnce=(from,to)=>{assert.equal(lua.split(from).length,2,'anchor: '+from.slice(0,60));lua=lua.replace(from,()=>to);};

// Device finding (D3): hidden-but-active text subtrees make each runtime B instantiation extremely slow on mobile.
// Every load starts with all large text subtrees inactive; completion re-enables only the ones the target mode draws.
replaceOnce('local function loadingRequest(mode,choices)\n',`resourceGate.heavyNames={'HomeScreen','SelectScreen','Portrait1','Portrait2','CountryStage'}
resourceGate.heavyKeep={menu={HomeScreen=true,SelectScreen=true,Portrait1=true,Portrait2=true},battle={CountryStage=true,Portrait1=true,Portrait2=true}}
resourceGate.setHeavy=function(mode)
 local nodes=resourceGate.heavyNodes
 if not nodes then
  -- Resolve and cache every node later code looks up while its subtree may be inactive.
  nodes={};resourceGate.heavyNodes=nodes
  for _,name in ipairs(resourceGate.heavyNames)do nodes[name]=loadingRoot:FindChild(name);rootNodes[name]=nodes[name]end
  for _,name in ipairs({'CountryStage','Portrait1','Portrait2'})do if nodes[name]then resourceGate.textNodes(nodes[name])end end
  if nodes.HomeScreen then for i=1,2 do local bust=nodes.HomeScreen:FindChild('HomeBust'..i);if bust then resourceGate.textNodes(bust)end end end
  if nodes.SelectScreen then for n=1,10 do local card=nodes.SelectScreen:FindChild('GridCard'..n);local face=card and card:FindChild('GridFace'..n);if face then resourceGate.textNodes(face)end end end
 end
 local keep=mode and resourceGate.heavyKeep[mode]or{}
 for _,name in ipairs(resourceGate.heavyNames)do local node=nodes[name];if node then node:SetActive(keep[name]==true)end end
end
local function loadingRequest(mode,choices)
`);
replaceOnce(" resourceGate.loader.stats={created=0,"," resourceGate.setHeavy(nil);resourceGate.loader.stats={created=0,");
replaceOnce("  if loadingState=='complete'then\n   resourceGate.mode=loadingTarget;resourceGate.busy=false\n","  if loadingState=='complete'then\n   resourceGate.setHeavy(loadingTarget)\n   resourceGate.mode=loadingTarget;resourceGate.busy=false\n");

// Keep the on-screen loading status from the mobile diagnostics; it is the only device-side evidence channel.
replaceOnce('local function loadingDraw(dt)\n','local function loadingDraw(dt)\n if dt and dt>0 then resourceGate.loader.lastDt=dt end\n');
const anchor=' local ratio=loadingTotal>0 and math.min(1,loadingDone/loadingTotal)or 1';
replaceOnce(anchor,` if loadingTarget=='battle' or resourceGate.waitingForBattle() then
  local s=resourceGate.loader.stats or {};local phase=#loadingDecode>0 and 'DECODE' or(#loadingUnload>0 and 'RECYCLE' or(#loadingQueue>0 and 'CREATE' or(resourceGate.loader.stagePaint and resourceGate.loader.stagePaint.n<=#resourceGate.loader.stagePaint.frame.chunks and 'PAINT' or string.upper(tostring(loadingState)))))
  loadingLabel.text=string.format('T1 %s | decode %d left %d | create %d/%d | task %d/%d | dt %dms',phase,s.decoded or 0,#loadingDecode,s.created or 0,(s.created or 0)+#loadingQueue,loadingDone,loadingTotal,math.floor((resourceGate.loader.lastDt or 0)*1000+.5));loadingLabel:SetVisible(true)
 end
`+anchor);
for(const line of dataLines)assert(lua.includes(line),'original text data altered');

const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date()).map(v=>[v.type,v.value]));
const stamp=p.year+p.month+p.day+'_'+p.hour+p.minute+p.second,out='outputs/training-room-mobile-fix-'+stamp,name='gpt_'+stamp+'_训练室手机优化_A';
fs.mkdirSync(out,{recursive:true});
for(const s of native.assets.scripts){s.source=lua;s.filename=name+'.lua';s.path=name+'.lua';}
native.assets.server.root.name=name;native.assets.server.meta.name=name;native.assets.server.meta.giaFileName=name+'.gia';
native.meta={...native.meta,name:'训练室版：手机加载优化'};
const a=exportGia(native.assets.server,{scripts:native.assets.scripts});assert(validateServerGiaCompatibility(a.buffer).valid);
fs.writeFileSync(out+'/'+name+'.gia',a.buffer);fs.writeFileSync(out+'/fighter.save.json',JSON.stringify(native));fs.writeFileSync(out+'/完整游戏.lua',lua);
const actual=importGia(a.buffer,name+'.gia');assert.equal(actual.scripts[0].source,lua);
save.meta={...save.meta,name:native.meta.name};save.assets.server=actual.project;save.assets.scripts=actual.scripts;
for(const s of save.assets.scripts){const hits=[];const walk=n=>{if((n.scriptMappingIds||[]).includes(s.guid))hits.push(n);for(const c of n.children||[])walk(c);};walk(actual.project.root);assert.equal(hits.length,1);s.controlId=hits[0].id;}
fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(save));
let controls=0;const count=n=>{controls++;for(const c of n.children||[])count(c);};count(actual.project.root);
const report={base,initialClientControls:controls-1,sourceBytes:Buffer.byteLength(lua),giaBytes:a.buffer.length,heavySubtreesInactiveDuringLoad:['HomeScreen','SelectScreen','Portrait1','Portrait2','CountryStage'],loadingDiagnosticText:true,originalTextTablesSha256:crypto.createHash('sha256').update(dataLines.join('\n')).digest('hex'),deviceVerified:false};
fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2));
fs.writeFileSync(out+'/实机测试说明.md',`# 训练室版：手机加载优化\n\n本版A：${name}.gia。基于 052337 头像训练室恢复版，素材、角色、规则与GF10不变。\n\n改动：依据D3真机结果，每次资源加载开始时停用训练室、首页、选人页和两侧大头像这些大文字子树；加载完成后只启用当前模式需要的部分（菜单：首页、选人、大头像；战斗：训练室、大头像）。训练室文字在加载期间写入，图元创建完成后才启用显示。\n\n进度条下保留诊断行：T1 阶段 | decode | create | task | dt。阶段 DECODE → CREATE → PAINT → READY。\n\n替换双方A，沿用B、GF10与变量，核对B外层索引。\n\n注意：本版初始客户端控件${report.initialClientControls}个，与此前真机启动失败的九角色高清候选同一量级。若进入试玩只有默认3D场景、没有任何界面，属于预置控件树过大的启动问题，与本次加载优化无关，请反馈该现象。若能启动，请录屏记录 CREATE 速度、进入训练室瞬间是否卡顿或闪退，以及三局切换与回选。\n`);
fs.writeFileSync('work/training-room-mobile-fix-latest.json',JSON.stringify({out,name,stamp,base},null,2));
console.log(JSON.stringify({out,name,...report}));
