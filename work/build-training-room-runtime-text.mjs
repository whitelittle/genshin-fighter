import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {exportGia,importGia,validateServerGiaCompatibility,validateGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
// Device finding (074356): 17,813 preset client controls never start. The 13,001 training-room text rows move to
// runtime instances of a separate C template; preset tree returns to the 050817 scale.
const base=JSON.parse(fs.readFileSync('work/training-room-mobile-fix-latest.json')).out;
const save=JSON.parse(fs.readFileSync(base+'/simulator.save.json'));
const native=JSON.parse(fs.readFileSync(base+'/fighter.save.json'));
// Editor finding: controls with GUIDs at 1078000000+ were dropped and the whole A preview went empty; keep every
// GUID inside the original 2^30..2^30+2^22 band.
const GUID_LIMIT=1073741824+4194304;
const GROUP=16,C_ROOT_GUID=1077900000,C_TEMPLATE_GUID=1077900001;
const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean);
let lua=native.assets.scripts[0].source;
const dataLines=['local portraitData=','local thumbData=','resourceGate.homePortraitData=','local Collision='].map(prefix=>lua.split('\n').find(line=>line.startsWith(prefix)));
assert(dataLines.every(Boolean));
const replaceOnce=(from,to)=>{assert.equal(lua.split(from).length,2,'anchor: '+from.slice(0,70));lua=lua.replace(from,()=>to);};

replaceOnce('local PIXEL_TEMPLATE_INDEX=1073742822\n',`local PIXEL_TEMPLATE_INDEX=1073742822
local TEXT_TEMPLATE_INDEX=${C_TEMPLATE_GUID} -- C outer container actual index
resourceGate.stageText={groups=0,size=${GROUP},instances={}}
`);
replaceOnce(' loadingTotal=loadingTotal+#loadingQueue+#loadingUnload\n',` resourceGate.loader.textCreate=0
 if mode=='battle'then local frame=resourceGate.stageFrame();local st=resourceGate.stageText;local need=math.ceil(#frame.chunks/st.size)-st.groups;if need>0 then resourceGate.loader.textCreate=need;loadingTotal=loadingTotal+need end end
 loadingTotal=loadingTotal+#loadingQueue+#loadingUnload
`);
// Text rows are created only after every B pixel exists, while CountryStage is still inactive, and before painting.
replaceOnce('  item=table.remove(loadingQueue);if not item then\n',`  item=table.remove(loadingQueue);if not item then
   if (resourceGate.loader.textCreate or 0)>0 then
    local st=resourceGate.stageText;local parent=rootNode('CountryStage')
    local box=game.InstantiateClientUIControl(TEXT_TEMPLATE_INDEX,parent);if not box then error('C text template missing: TEXT_TEMPLATE_INDEX='..tostring(TEXT_TEMPLATE_INDEX))end
    local c=resourceGate.textNodes(parent);local first=st.groups*st.size
    for j=1,st.size do local node=box:FindChild('TextArt'..j);if not node then error('C template lacks TextArt'..j)end;node.name='TextArt'..(first+j);node:SetVisible(false);c.nodes[first+j]=node end
    st.groups=st.groups+1;st.instances[st.groups]=box;resourceGate.loader.textCreate=resourceGate.loader.textCreate-1;resourceGate.loader.stats.textGroups=(resourceGate.loader.stats.textGroups or 0)+1
    loadingDone=loadingDone+1;return true
   end
`);
replaceOnce("#loadingQueue>0 and 'CREATE' or(resourceGate.loader.stagePaint","#loadingQueue>0 and 'CREATE' or((resourceGate.loader.textCreate or 0)>0 and 'TEXT' or(resourceGate.loader.stagePaint");
replaceOnce("string.upper(tostring(loadingState)))))","string.upper(tostring(loadingState))))))");
replaceOnce("loadingLabel.text=string.format('T1 %s","loadingLabel.text=string.format('T2 %s");
replaceOnce("*1000+.5));loadingLabel:SetVisible(true)","*1000+.5))..string.format(' | text %d/%d',resourceGate.stageText.groups,resourceGate.stageText.groups+(resourceGate.loader.textCreate or 0));loadingLabel:SetVisible(true)");
for(const line of dataLines)assert(lua.includes(line),'original text data altered');

// A: drop the preset training-room rows, keep the CountryStage container.
const stage=find(native.assets.server.root,'CountryStage');
const proto=structuredClone(stage.children.find(c=>/^TextArt\d+$/.test(c.name)));assert(proto&&proto.kind==='textbox');
const removedStageRows=stage.children.length;stage.children=[];
let removedFrames=0;
const stripFrames=n=>{const before=(n.children||[]).length;n.children=(n.children||[]).filter(c=>!/^PortraitFrame/.test(c.name));removedFrames+=before-n.children.length;n.children.forEach(stripFrames);};
stripFrames(native.assets.server.root);

// C: one container holding GROUP rows cloned from the original stage row (same font/alignment fields).
const client=structuredClone(save.assets.client);
const bTemplate=find(client.root,'LoadingPixelTemplate');assert(bTemplate);
const template=structuredClone(bTemplate);template.id='stage_text_template';template.guid=C_TEMPLATE_GUID;template.name='StageTextTemplate';delete template.scriptMappingIds;
template.children=Array.from({length:GROUP},(_,i)=>{const n=structuredClone(proto);n.id='stage_text_row_'+(i+1);n.guid=C_TEMPLATE_GUID+1+i;n.name='TextArt'+(i+1);n.visible=false;n.text='';n.scriptMappingIds=[];n.giaRelatedGuids=[];return n;});

const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date()).map(v=>[v.type,v.value]));
const stamp=p.year+p.month+p.day+'_'+p.hour+p.minute+p.second,out='outputs/training-room-runtime-text-'+stamp,name='gpt_'+stamp+'_训练室运行时文字_A',cName='gpt_'+stamp+'_训练室文字模板_C';
fs.mkdirSync(out,{recursive:true});
client.root.guid=C_ROOT_GUID;client.root.name=cName;client.root.children=[template];client.meta={...client.meta,name:cName,giaFileName:cName+'.gia',giaFileId:C_ROOT_GUID};

for(const s of native.assets.scripts){s.source=lua;s.filename=name+'.lua';s.path=name+'.lua';}
native.assets.server.root.name=name;native.assets.server.meta.name=name;native.assets.server.meta.giaFileName=name+'.gia';
native.meta={...native.meta,name:'训练室版：运行时文字'};
const guidsInBand=n=>(n.guid==null||n.guid<GUID_LIMIT)&&(n.children||[]).every(guidsInBand);
assert(guidsInBand(native.assets.server.root),'A GUID out of band');assert(guidsInBand(client.root),'C GUID out of band');
const a=exportGia(native.assets.server,{scripts:native.assets.scripts});assert(validateServerGiaCompatibility(a.buffer).valid);
const c=exportGia(client);assert(validateGiaCompatibility(c.buffer).valid);
fs.writeFileSync(out+'/'+name+'.gia',a.buffer);fs.writeFileSync(out+'/'+cName+'.gia',c.buffer);
fs.writeFileSync(out+'/fighter.save.json',JSON.stringify(native));fs.writeFileSync(out+'/完整游戏.lua',lua);

// Simulator save uses what the exported GIAs read back as; B and C sit side by side in the client templates.
const aa=importGia(a.buffer,name+'.gia');assert.equal(aa.scripts[0].source,lua);
const cc=importGia(c.buffer,cName+'.gia');const cTemplate=find((cc.clientProject||cc.project).root,'StageTextTemplate');assert(cTemplate);assert.equal(cTemplate.children.length,GROUP);
save.meta={...save.meta,name:native.meta.name};save.assets.server=aa.project;save.assets.scripts=aa.scripts;
save.assets.client.root.children=save.assets.client.root.children.filter(n=>n.name!=='StageTextTemplate').concat([cTemplate]);
for(const s of save.assets.scripts){const hits=[];const walk=n=>{if((n.scriptMappingIds||[]).includes(s.guid))hits.push(n);for(const c of n.children||[])walk(c);};walk(aa.project.root);assert.equal(hits.length,1);s.controlId=hits[0].id;}
fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(save));

let controls=0;const count=n=>{controls++;for(const c of n.children||[])count(c);};count(aa.project.root);
assert.equal(removedFrames,10);
const report={base,initialClientControls:controls-1,removedStageRows,removedPortraitFrames:removedFrames,guidLimit:GUID_LIMIT,textTemplateGroup:GROUP,textTemplateIndexDefault:C_TEMPLATE_GUID,sourceBytes:Buffer.byteLength(lua),giaABytes:a.buffer.length,giaCBytes:c.buffer.length,originalTextTablesSha256:crypto.createHash('sha256').update(dataLines.join('\n')).digest('hex'),deviceVerified:false};
fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2));
fs.writeFileSync(out+'/实机测试说明.md',`# 训练室版：运行时文字\n\n074356 因预置控件 17,813 个无法启动。本版把训练室 ${removedStageRows} 个文字块从A中移除，进入第一场战斗加载时用文字模板C运行时创建（每个C含${GROUP}块，共约${Math.ceil(removedStageRows/GROUP)}次实例化），三局共用。A初始客户端控件 ${report.initialClientControls} 个。075742 的A在编辑器中为空，原因是两侧大头像的 10 个边框控件 GUID 落在 1078000000 号段（082750 删除后恢复黑屏预览）；本版去掉这些边框，C 的 GUID 也改到 ${C_ROOT_GUID} 起，A、C 所有 GUID 都小于 ${GUID_LIMIT}。画质、角色、规则、GF10不变；加载期间停用大文字子树的优化保留。\n\n## 导入步骤\n\n1. 客户端控件模板导入 ${cName}.gia，记下 StageTextTemplate 最外层容器的实际索引（不是 TextArt 子控件）。原 B 模板保留不动。\n2. 双方 A 换成 ${name}.gia。打开主 Lua：PIXEL_TEMPLATE_INDEX 照旧填 B 外层索引；新的 TEXT_TEMPLATE_INDEX 填上一步 C 的外层索引。保存。\n3. 沿用 GF10、十信号和17变量。\n\n## 观察\n\n进度条下诊断行：T2 阶段 | decode | create | task | dt | text 已建组/总组。阶段 DECODE → CREATE → TEXT → PAINT → READY。\n\n若出现 “C text template missing”，说明 TEXT_TEMPLATE_INDEX 未填对。请录屏记录 TEXT 阶段速度、进入训练室瞬间、三局切换与回选。\n`);
fs.writeFileSync('work/training-room-runtime-text-latest.json',JSON.stringify({out,name,cName,stamp,base},null,2));
console.log(JSON.stringify({out,name,cName,...report}));
