import fs from 'node:fs';
import assert from 'node:assert/strict';
import {exportGia,importGia,validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
// Probe: the battle page is the first and only screen. Training room (runtime C text) + two idle fighters + battle UI,
// no home/select page ever painted and no server signal ever sent. Measures whether the phone can hold the battle
// scene on its own.
const base=JSON.parse(fs.readFileSync('work/training-room-runtime-text-latest.json'));
const indices=JSON.parse(fs.readFileSync('work/device-template-indices.json'));
const save=JSON.parse(fs.readFileSync(base.out+'/simulator.save.json'));
const native=JSON.parse(fs.readFileSync(base.out+'/fighter.save.json'));
let lua=native.assets.scripts[0].source;
const once=(from,to)=>{assert.equal(lua.split(from).length,2,'anchor: '+from.slice(0,70));lua=lua.replace(from,()=>to);};

lua='BATTLE_HOME={}\n'+lua;
// Stage accessors only exist after the first load runs init, so boot loads in a neutral mode that paints neither
// home nor select, then switches straight to battle.
once("local menuMode='home'\n","local menuMode='probe'\n");
for(const fn of ['helloRequest','joinRequest','sendSelection']){const re=new RegExp(`local function ${fn}\\(\\)[ \\t\\r]*\\n`,'g');assert.equal((lua.match(re)||[]).length,1,fn);lua=lua.replace(re,m=>m+' if BATTLE_HOME then return end\n');}
once(" if not onlineReady or not rb then\n  menuDraw()\n"," if not onlineReady or not rb then\n  if BATTLE_HOME and not resourceGate.busy then\n   if not BATTLE_HOME.requested then BATTLE_HOME.requested=true;menuMode='battle';menuDirty=true;resourceGate.request('battle',{1,2});return end\n   if not BATTLE_HOME.started then BATTLE_HOME.started=true;restart()end;draw();Collision.drawBoxes()\n  end\n  menuDraw()\n");
once("loadingLabel.text=string.format('T2 %s","loadingLabel.text=string.format('P1 %s");
// Phone UI canvas is narrower than the screen; the stretch-anchored covers grow half a canvas past each edge.
once("resourceGate.loader.canvasW=cw;resourceGate.loader.canvasH=ch;resourceGate.loader.barWidth=nil","resourceGate.loader.canvasW=cw;resourceGate.loader.canvasH=ch;resourceGate.loader.barWidth=nil\n  do local bk=loadingRoot:FindChild('FullscreenBacking');if bk then bk:SetSizeDelta(cw,ch)end;local black=loadingOverlay:FindChild('LoadingBlack');if black then black:SetSizeDelta(cw,ch)end end");
const deviceLua=lua.replace(/local PIXEL_TEMPLATE_INDEX=\d+\n/,'local PIXEL_TEMPLATE_INDEX='+indices.PIXEL_TEMPLATE_INDEX+'\n').replace(/local TEXT_TEMPLATE_INDEX=\d+/,'local TEXT_TEMPLATE_INDEX='+indices.TEXT_TEMPLATE_INDEX);
assert(deviceLua.includes('local PIXEL_TEMPLATE_INDEX='+indices.PIXEL_TEMPLATE_INDEX+'\n')&&deviceLua.includes('local TEXT_TEMPLATE_INDEX='+indices.TEXT_TEMPLATE_INDEX));

const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date()).map(v=>[v.type,v.value]));
const stamp=p.year+p.month+p.day+'_'+p.hour+p.minute+p.second,out='outputs/battle-home-probe-'+stamp,name='gpt_'+stamp+'_战斗首页探针_A';
fs.mkdirSync(out,{recursive:true});
for(const s of native.assets.scripts){s.source=deviceLua;s.filename=name+'.lua';s.path=name+'.lua';}
native.assets.server.root.name=name;native.assets.server.meta.name=name;native.assets.server.meta.giaFileName=name+'.gia';
native.meta={...native.meta,name:'战斗首页探针'};
const a=exportGia(native.assets.server,{scripts:native.assets.scripts});assert(validateServerGiaCompatibility(a.buffer).valid);
fs.writeFileSync(out+'/'+name+'.gia',a.buffer);fs.writeFileSync(out+'/fighter.save.json',JSON.stringify(native));fs.writeFileSync(out+'/完整游戏.lua',deviceLua);
const aa=importGia(a.buffer,name+'.gia');assert.equal(aa.scripts[0].source,deviceLua);
// Simulator keeps its own B/C template indices.
save.meta={...save.meta,name:native.meta.name};save.assets.server=aa.project;save.assets.scripts=aa.scripts.map(s=>({...s,source:lua}));
for(const s of save.assets.scripts){const hits=[];const walk=n=>{if((n.scriptMappingIds||[]).includes(s.guid))hits.push(n);for(const c of n.children||[])walk(c);};walk(aa.project.root);assert.equal(hits.length,1);s.controlId=hits[0].id;}
fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(save));
const report={base:base.out,cTemplate:base.cName,indices:{PIXEL_TEMPLATE_INDEX:indices.PIXEL_TEMPLATE_INDEX,TEXT_TEMPLATE_INDEX:indices.TEXT_TEMPLATE_INDEX},sourceBytes:Buffer.byteLength(deviceLua),giaABytes:a.buffer.length,deviceVerified:false};
fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2));
fs.writeFileSync(out+'/实机测试说明.md',`# 战斗首页探针（P1）\n\n开机直接进入战斗页面：训练室（运行时用文字模板C创建）+ 刻晴、迪卢克两个站立角色 + 战斗界面。不显示首页和选人页，也不发送任何联网信号，单人即可测试。角色不会动，回合不会推进。\n\n## 导入\n\n只需要这一个 A，B 和 C 沿用已导入的版本。索引已写入：PIXEL_TEMPLATE_INDEX=${indices.PIXEL_TEMPLATE_INDEX}（B通用图元），TEXT_TEMPLATE_INDEX=${indices.TEXT_TEMPLATE_INDEX}（C文字控件），无需手改。\n\n## 观察\n\n读条下方的诊断行以 P1 开头，显示 DECODE、CREATE、TEXT、PAINT 各阶段和 text x/813。请记录：能否进入画面；若闪退，闪退前停在哪个阶段、数字是多少；进入后画面是否完整、是否卡顿，左右两侧是否露出3D场景。\n`);
fs.writeFileSync('work/battle-home-probe-latest.json',JSON.stringify({out,name,stamp,base:base.out},null,2));
console.log(JSON.stringify({out,name,...report}));
