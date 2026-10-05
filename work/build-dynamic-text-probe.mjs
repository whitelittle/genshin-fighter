import fs from 'node:fs';import assert from 'node:assert/strict';
import {exportGia,importGia,validateServerGiaCompatibility,validateGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {renderScenePng} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';
const old=JSON.parse(fs.readFileSync('work/minimal-native-ui-latest.json'));const save=JSON.parse(fs.readFileSync(old.out+'/fighter.save.json')),simBase=JSON.parse(fs.readFileSync(old.out+'/reimported.simulator.save.json'));const baseline=JSON.parse(fs.readFileSync('outputs/full-reinstall/fighter.save.json'));
const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date()).map(v=>[v.type,v.value]));const stamp=p.year+p.month+p.day+'_'+p.hour+p.minute+p.second;
const out='outputs/dynamic-text-probe-'+stamp,aName='gpt_'+stamp+'_动态文字探针_A',cName='gpt_'+stamp+'_文字模板_C',moduleName='DynamicTextRows_'+stamp;fs.mkdirSync(out,{recursive:true});
const host=save.assets.server.root.children[0],label=host.children[0];label.text='DYNAMIC TEXT / LUA WAIT';
const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean);
const back=structuredClone(find(baseline.assets.server.root,'LoadingBlack'));back.id='dynamic_probe_back';back.guid=1078200100;back.name='ProbeBlack';back.active=true;back.visible=true;back.children=[];for(const t of Object.values(back.transformByPlatform)){t.anchorMin={x:0,y:0};t.anchorMax={x:1,y:1};t.offset={x:0,y:0};t.size={x:0,y:0};}host.children.push(back);
const client=structuredClone(baseline.assets.client);client.root.guid=1078200000;client.root.name=cName;client.meta.name=cName;client.meta.giaFileName=cName+'.gia';client.meta.giaFileId=client.root.guid;
const template=client.root.children[0];template.id='dynamic_text_template';template.guid=1078200001;template.name='DynamicTextTemplate';template.children=[];const text=structuredClone(label);text.id='dynamic_text_seed';text.guid=1078200002;text.name='TextPixel';text.text='';text.visible=true;text.bgColor=0;text.fontSize=20;text.minimumFontSize=20;text.enableOutline=false;text.horizontalAlignment='Left';text.verticalAlignment='Top';delete text.giaRaw.textAlign;delete text.giaRaw.textVerticalAlign;delete text.scriptMappingIds;for(const t of Object.values(text.transformByPlatform)){t.offset={x:0,y:0};t.size={x:160,y:40};t.scale={x:1,y:1,z:1};}template.children=[text];
const rows=Array.from({length:64},(_,i)=>`{x=${(i%8)*110-385},y=${120-Math.floor(i/8)*40},text="\\226\\150\\136\\226\\150\\136\\226\\150\\136\\226\\150\\136"}`).join(',');const data='return {rows={'+rows+'}}\n';
const lua=`local TEXT_TEMPLATE_INDEX=1078200001 -- C outer container actual index
local rows,created,timer,failed={},0,0,false
local function status(s)local n=script.object:FindChild('NativeBootProbe');n.text=s;n:SetVisible(true);n:SetAsLastSibling()end
function OnInit()status('LUA INIT OK / waiting for module');script:EnableUpdate(true)end
function OnStart()
 local ok,result=pcall(require,'default_import_file/${moduleName}')
 if not ok then failed=true;status('MODULE ERROR: '..tostring(result));return end
 rows=result.rows;status('MODULE OK / 0 / '..#rows);script:EnableUpdate(true)
end
function OnUpdate(dt)
 if failed or #rows==0 or created>=#rows then return end
 timer=timer+dt;if timer<0.1 then return end;timer=0
 local ok,err=pcall(function()
  local row=rows[created+1]
  local box=game.InstantiateClientUIControl(TEXT_TEMPLATE_INDEX,script.object)
  if not box then error('C template not found: '..TEXT_TEMPLATE_INDEX)end
  local n=box:FindChild('TextPixel');if not n then error('C missing TextPixel')end
  box.name='DynamicText'..(created+1);box:SetAnchoredPosition(row.x,row.y);box:SetAsLastSibling()
  n.text=row.text;n:SetVisible(true);box:SetVisible(true)
  created=created+1;status((created==#rows and 'DYNAMIC TEXT OK / 'or'CREATING / ')..created..' / '..#rows)
 end)
 if not ok then failed=true;status('CREATE ERROR: '..tostring(err))end
end
`;
save.assets.server.root.name=aName;save.assets.server.meta.name=aName;save.assets.server.meta.giaFileName=aName+'.gia';const main=save.assets.scripts[0];main.source=lua;main.path=aName+'.lua';main.filename=aName+'.lua';save.assets.scripts=[main,{id:'1078200030',guid:1078200030,path:moduleName+'.lua',filename:moduleName+'.lua',source:data,controlId:''}];save.assets.client=client;
const a=exportGia(save.assets.server,{scripts:save.assets.scripts}),c=exportGia(client);assert(validateServerGiaCompatibility(a.buffer).valid);assert(validateGiaCompatibility(c.buffer).valid);fs.writeFileSync(out+'/'+aName+'.gia',a.buffer);fs.writeFileSync(out+'/'+cName+'.gia',c.buffer);fs.writeFileSync(out+'/fighter.save.json',JSON.stringify(save));fs.writeFileSync(out+'/主脚本.lua',lua);fs.writeFileSync(out+'/文字数据.lua',data);
const aa=importGia(a.buffer,aName+'.gia'),cc=importGia(c.buffer,cName+'.gia');const sim=structuredClone(simBase);sim.assets.server=aa.project;sim.assets.client=cc.clientProject||cc.project;sim.assets.scripts=aa.scripts;
for(const s of sim.assets.scripts){const matches=[];const walk=n=>{if((n.scriptMappingIds||[]).includes(s.guid))matches.push(n);for(const c of n.children||[])walk(c);};walk(aa.project.root);if(matches.length){assert.equal(matches.length,1);s.controlId=matches[0].id;}}
fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(sim));
const studio=createStudio(sim);studio.playStart();for(let i=0;i<550;i++)studio.playStep(1/60,{observe:false});const state=studio.playGet({view:true,paint:true});const n=state.scene.nodes.find(n=>n.name==='NativeBootProbe');assert(n&&n.text==='DYNAMIC TEXT OK / 64 / 64',JSON.stringify({text:n?.text,logs:state.logs}));assert.equal(state.scene.nodes.filter(n=>n.name==='TextPixel').length,64);assert(!state.logs.some(l=>['error','lua-error'].includes(l.level)));fs.writeFileSync(out+'/动态文字模拟器.png',renderScenePng(state.scene,state.canvasWidth,state.canvasHeight).data);studio.playStop();
const wrong=structuredClone(sim);wrong.assets.scripts.find(s=>s.controlId).source=lua.replace('TEXT_TEMPLATE_INDEX=1078200001','TEXT_TEMPLATE_INDEX=1078200999');const ws=createStudio(wrong);ws.playStart();for(let i=0;i<30;i++)ws.playStep(1/60,{observe:false});const error=ws.playGet({view:true}).scene.nodes.find(n=>n.name==='NativeBootProbe');assert(/CREATE ERROR/.test(error.text));ws.playStop();
fs.writeFileSync(out+'/verification.json',JSON.stringify({exportedGiaReimport:true,requireModule:true,dynamicTexts:64,batchInterval:.1,wrongIndexVisibleError:true,initialAClientControls:3,templateClientControls:2,giaABytes:a.buffer.length,giaCBytes:c.buffer.length,native:false},null,2));
fs.writeFileSync(out+'/说明.md','# 动态文字与数据Lua探针\n\n独立测试，不是完整游戏：小A含3控件，独立数据Lua内嵌A且不挂载，require读取64条纯方块文字数据，每0.1秒创建一个C文字模板。默认有黑底和状态条，错误可见。高清正式素材未修改。\n\n1. 客户端控件模板导入'+cName+'.gia，记下DynamicTextTemplate最外层容器实际索引，不用TextPixel子控件索引。\n2. 默认布局使用服务器A '+aName+'.gia，打开FighterDemo主Lua，把首行TEXT_TEMPLATE_INDEX填为上一步实际索引并保存。数据Lua已包含，不另挂。\n3. 保存后重新试玩，约7.5秒后预期DYNAMIC TEXT OK / 64 / 64及白色方块。B和GF10节点均不修改。\n\n程序/模拟器：实际导出的A和C回读后，模块require及64实例动态创建通过；错误C索引显示CREATE ERROR；文字直接渲染，无PNG替代。真机：尚待观察；不宣称正式demo修复。\n');fs.writeFileSync('work/dynamic-text-probe-latest.json',JSON.stringify({out,aName,cName,stamp}));console.log(JSON.stringify({out,aName,cName,simulator:true}));
