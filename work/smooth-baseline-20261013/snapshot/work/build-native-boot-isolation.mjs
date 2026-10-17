import fs from 'node:fs';import assert from 'node:assert/strict';
import {exportGia,importGia,validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
const latest=JSON.parse(fs.readFileSync('work/nine-role-hd-latest.json'));const save=JSON.parse(fs.readFileSync(latest.out+'/fighter.save.json'));const sim=JSON.parse(fs.readFileSync(latest.out+'/simulator.save.json'));
const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date()).map(v=>[v.type,v.value]));const stamp=p.year+p.month+p.day+'_'+p.hour+p.minute+p.second;
const out='outputs/native-boot-isolation-'+stamp,name='gpt_'+stamp+'_启动挂载排错_A';fs.mkdirSync(out,{recursive:true});
const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean);const host=find(save.assets.server.root,'FighterDemo'),label=find(host,'BootDiagnostic');
label.name='NativeBootProbe';label.text='UI MOUNTED / LUA WAIT';label.visible=true;label.active=true;label.fontSize=30;label.minimumFontSize=30;label.bgColor=0xff172131;label.fontColor=0xffffffff;label.horizontalAlignment='Middle';label.verticalAlignment='Middle';delete label.giaRaw.textAlign;delete label.giaRaw.textVerticalAlign;
for(const t of Object.values(label.transformByPlatform)){t.offset={x:0,y:300};t.size={x:1000,y:100};t.scale={x:1,y:1,z:1};}
host.children=host.children.filter(c=>c!==label);host.children.unshift(label);
const source=`local ticks=0
local function mark(s)
 local n=script.object:FindChild('NativeBootProbe')
 if n then n.text=s;n:SetActive(true);n:SetVisible(true);n:SetAsFirstSibling()end
end
function OnInit()mark('LUA INIT OK');script:EnableUpdate(true)end
function OnStart()mark('LUA START OK');script:EnableUpdate(true)end
function OnUpdate(dt)ticks=ticks+1;mark('LUA UPDATE OK / '..ticks)end
`;
save.assets.scripts[0].source=source;save.assets.scripts[0].filename=name+'.lua';save.assets.scripts[0].path='lua/'+name+'.lua';save.assets.server.root.name=name;save.assets.server.meta.name=name;save.assets.server.meta.giaFileName=name+'.gia';
sim.assets.server=structuredClone(save.assets.server);sim.assets.scripts=structuredClone(save.assets.scripts);fs.writeFileSync(out+'/fighter.save.json',JSON.stringify(save));fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(sim));fs.writeFileSync(out+'/启动排错.lua',source);
const r=exportGia(save.assets.server,{scripts:save.assets.scripts});assert(validateServerGiaCompatibility(r.buffer).valid);const re=importGia(r.buffer,name+'.gia');assert(re.scripts.some(s=>s.source===source));fs.writeFileSync(out+'/'+name+'.gia',r.buffer);
const studio=createStudio(sim);studio.playStart();for(let i=0;i<10;i++)studio.playStep(1/60,{observe:false});const state=studio.playGet({view:true});const n=state.scene.nodes.find(n=>n.name==='NativeBootProbe');assert(n);assert(/LUA UPDATE OK/.test(n.text));assert(!state.logs.some(l=>['error','lua-error'].includes(l.level)));studio.playStop();
fs.writeFileSync(out+'/verification.json',JSON.stringify({sameControlTree:true,onlyShortScript:true,exportRoundtrip:true,simulatorStartup:true,nativeStartup:false,giaBytes:r.buffer.length,probeText:n.text},null,2));
fs.writeFileSync(out+'/说明.md','# 启动挂载排错\n\n这是排错包，不是完整游戏。保留九角色候选的全部控件树，只把8.54MB游戏脚本换成短启动脚本，显示独立可见诊断框。原高清数据与候选不改动。只替换玩家A进行一次试玩，不需要B索引，也不改节点。\n\n若显示UI MOUNTED / LUA WAIT，界面已实例化而Lua未执行；若显示LUA UPDATE OK与递增数字，同样控件树和短脚本在真机启动；若仍完全没有框，界面挂载或原生导入需要进一步检查，不能归因于大脚本。\n\n程序：兼容检查与脚本往返通过。模拟器：正式排错包同样控件树，启动及更新诊断通过。真机：待匿名玩家提供观察；不声明修复完成。\n');
fs.writeFileSync('work/native-boot-isolation-latest.json',JSON.stringify({out,name,stamp}));console.log(JSON.stringify({out,name,simulatorStartup:true,probeText:n.text}));
