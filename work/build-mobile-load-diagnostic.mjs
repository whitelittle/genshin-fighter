import fs from 'node:fs';
import assert from 'node:assert/strict';
import {exportGia,importGia,validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const variant=process.env.DIAG_VARIANT||'menu';
assert(['menu','basic','menu-deactivate','menu-deactivate-v2','battle-deactivate-cover'].includes(variant));
const baseLatest=variant==='basic'?'work/basic-demo-latest.json':'work/menu-art-return-latest.json';
const coverFix=variant==='battle-deactivate-cover';
const deactivateMenu=variant==='menu-deactivate'||coverFix;
const deactivateMenuV2=variant==='menu-deactivate-v2';
const tag={menu:'D1',basic:'D2基础对照','menu-deactivate':'D3停用菜单','menu-deactivate-v2':'D4停用菜单修正','battle-deactivate-cover':'D5战斗停用与遮挡'}[variant];
// Indices the user's editor assigned on import; written in so the Lua needs no manual edit.
const indices=JSON.parse(fs.readFileSync('work/device-template-indices.json'));
const base=JSON.parse(fs.readFileSync(baseLatest)).out;
const save=JSON.parse(fs.readFileSync(base+'/simulator.save.json'));
const native=JSON.parse(fs.readFileSync(base+'/fighter.save.json'));
let lua=native.assets.scripts[0].source;
const anchor=' local ratio=loadingTotal>0 and math.min(1,loadingDone/loadingTotal)or 1';
assert.equal(lua.split(anchor).length,2);
lua=lua.replace('local function loadingDraw(dt)\n',()=>'local function loadingDraw(dt)\n if dt and dt>0 then resourceGate.loader.lastDt=dt end\n');
assert(lua.includes('resourceGate.loader.lastDt=dt'));
// Display-only probe: loading order, batch sizes and control counts stay identical to the base build.
lua=lua.replace(anchor,()=>` if loadingTarget=='battle' or resourceGate.waitingForBattle() then
  local s=resourceGate.loader.stats or {};local phase=#loadingDecode>0 and 'DECODE' or(#loadingUnload>0 and 'RECYCLE' or(#loadingQueue>0 and 'CREATE' or string.upper(tostring(loadingState))))
  loadingLabel.text=string.format('${tag.slice(0,2)} %s | decode %d left %d | create %d/%d | task %d/%d | dt %dms',phase,s.decoded or 0,#loadingDecode,s.created or 0,(s.created or 0)+#loadingQueue,loadingDone,loadingTotal,math.floor((resourceGate.loader.lastDt or 0)*1000+.5));loadingLabel:SetVisible(true)
 end
`+anchor);
if(deactivateMenu){
 // Hidden menu text pools stay active by default; inactive subtrees should drop out of native canvas rebuilds.
 const req='local function loadingRequest(mode,choices)\n';
 assert(lua.includes(req));
 lua=lua.replace(req,()=>req+" do local battle=mode=='battle';for _,name in ipairs({'HomeScreen','SelectScreen'})do local n=loadingRoot:FindChild(name);if n then n:SetActive(not battle)end end end\n");
}
if(deactivateMenuV2){
 const once=(from,to)=>{assert.equal(lua.split(from).length,2,'anchor: '+from.slice(0,60));lua=lua.replace(from,()=>to);};
 // Device (D3): after one selection the client UI vanished into the 3D scene while the simulator passes; menus were
 // re-activated at the start of the menu load, so 4042 sprite destroys ran against ~4085 active menu controls.
 // Menus now stay inactive for every load and come back only when it completes. Every UI node is resolved while
 // still active, so no lookup ever has to search an inactive subtree.
 const req='local function loadingRequest(mode,choices)\n';
 once(req,req+` if not resourceGate.menuNodes then
  local function warm(name)local n=rootNodes[name];if n then return n end;local parent=uiParents[name]and warm(uiParents[name])or loadingRoot;n=parent and parent:FindChild(name);if n then rootNodes[name]=n end;return n end
  for name in pairs(uiParents)do warm(name)end
  resourceGate.menuNodes={warm('HomeScreen'),warm('SelectScreen')}
  for i=1,2 do local bust=rootNodes['HomeBust'..i]or(rootNodes.HomeScreen and rootNodes.HomeScreen:FindChild('HomeBust'..i));if bust then rootNodes['HomeBust'..i]=bust;resourceGate.textNodes(bust)end end
  for n=1,10 do local face=rootNodes['GridFace'..n];if face then resourceGate.textNodes(face)end end
 end
 for _,n in ipairs(resourceGate.menuNodes)do n:SetActive(false)end
`);
 once("   resourceGate.mode=loadingTarget;resourceGate.busy=false\n","   if loadingTarget=='menu'then for _,n in ipairs(resourceGate.menuNodes)do n:SetActive(true)end end\n   resourceGate.mode=loadingTarget;resourceGate.busy=false\n");
 // A runtime error used to hide every control, which on device looks exactly like falling back to the 3D scene.
 once(" for _,node in ipairs(loadingRoot:GetChildren())do node:SetVisible(node==panel)end\n"," for _,node in ipairs(loadingRoot:GetChildren())do node:SetVisible(node==panel or node.name=='FullscreenBacking')end\n");
 // Phone UI canvas is narrower than the screen; the stretch-anchored covers grow half a canvas past each edge.
 once("resourceGate.loader.canvasW=cw;resourceGate.loader.canvasH=ch;resourceGate.loader.barWidth=nil","resourceGate.loader.canvasW=cw;resourceGate.loader.canvasH=ch;resourceGate.loader.barWidth=nil\n  do local bk=loadingRoot:FindChild('FullscreenBacking');if bk then bk:SetSizeDelta(cw,ch)end;local black=loadingOverlay:FindChild('LoadingBlack');if black then black:SetSizeDelta(cw,ch)end end");
 once(" if loadingTarget=='battle' or resourceGate.waitingForBattle() then\n  local s=resourceGate.loader.stats"," do\n  local s=resourceGate.loader.stats");
 lua=lua.replace("loadingLabel.text=string.format('D4 %s |","loadingLabel.text=string.format('D4 '..string.upper(tostring(loadingTarget))..' %s |");
 const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean);
 for(const name of ['FullscreenBacking','LoadingBlack']){const n=find(native.assets.server.root,name);assert(n,name);for(const t of Object.values(n.transformByPlatform))assert(t.anchorMin.x===0&&t.anchorMax.x===1&&t.anchorMin.y===0&&t.anchorMax.y===1,name+' must be stretch-anchored');}
}
if(coverFix){
 const once=(from,to)=>{assert.equal(lua.split(from).length,2,'anchor: '+from.slice(0,60));lua=lua.replace(from,()=>to);};
 // D4 kept menus inactive for every load, so entering selection and every pick blanked the UI; abandoned.
 // D5 = D3 (menus inactive only while loading battle) plus the cover, error-screen and node-cache fixes.
 once('local PIXEL_TEMPLATE_INDEX=1073742822\n','local PIXEL_TEMPLATE_INDEX='+indices.PIXEL_TEMPLATE_INDEX+'\n');
 const req='local function loadingRequest(mode,choices)\n';
 once(req,req+` if not resourceGate.uiWarm then
  resourceGate.uiWarm=true
  local function warm(name)local n=rootNodes[name];if n then return n end;local parent=uiParents[name]and warm(uiParents[name])or loadingRoot;n=parent and parent:FindChild(name);if n then rootNodes[name]=n end;return n end
  for name in pairs(uiParents)do warm(name)end
  for _,name in ipairs({'HomeBust1','HomeBust2','GridFace1','GridFace2','GridFace3','GridFace4','GridFace5','GridFace6','GridFace7','GridFace8','GridFace9','GridFace10'})do local n=warm(name);if n then resourceGate.textNodes(n)end end
 end
`);
 // Menu loads (entering selection, every pick) keep the menu background; hiding it showed the 3D scene behind.
 once("loadingRoot:FindChild('FullscreenBacking'):SetVisible(false);loadingOverlay:SetActive(true)","loadingRoot:FindChild('FullscreenBacking'):SetVisible(mode~='battle');loadingOverlay:SetActive(true)");
 once(" if backing then backing:SetVisible(loadingState=='ready' and not resourceGate.waitingForBattle())end"," if backing then backing:SetVisible((loadingState=='ready' or loadingTarget~='battle') and not resourceGate.waitingForBattle())end");
 once(" for _,node in ipairs(loadingRoot:GetChildren())do node:SetVisible(node==panel)end\n"," for _,node in ipairs(loadingRoot:GetChildren())do node:SetVisible(node==panel or node.name=='FullscreenBacking')end\n");
 once("resourceGate.loader.canvasW=cw;resourceGate.loader.canvasH=ch;resourceGate.loader.barWidth=nil","resourceGate.loader.canvasW=cw;resourceGate.loader.canvasH=ch;resourceGate.loader.barWidth=nil\n  do local bk=loadingRoot:FindChild('FullscreenBacking');if bk then bk:SetSizeDelta(cw,ch)end;local black=loadingOverlay:FindChild('LoadingBlack');if black then black:SetSizeDelta(cw,ch)end end");
}
const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date()).map(v=>[v.type,v.value]));
const stamp=p.year+p.month+p.day+'_'+p.hour+p.minute+p.second,out='outputs/mobile-load-diagnostic-'+stamp,name='gpt_'+stamp+'_手机加载诊断'+tag+'_A';
fs.mkdirSync(out,{recursive:true});
for(const s of native.assets.scripts){s.source=lua;s.filename=name+'.lua';s.path=name+'.lua';}
native.assets.server.root.name=name;native.assets.server.meta.name=name;native.assets.server.meta.giaFileName=name+'.gia';
native.meta={...native.meta,name:'手机战斗加载诊断'};
const a=exportGia(native.assets.server,{scripts:native.assets.scripts});assert(validateServerGiaCompatibility(a.buffer).valid);
fs.writeFileSync(out+'/'+name+'.gia',a.buffer);fs.writeFileSync(out+'/fighter.save.json',JSON.stringify(native));fs.writeFileSync(out+'/完整游戏.lua',lua);
const actual=importGia(a.buffer,name+'.gia');assert.equal(actual.scripts[0].source,lua);
save.meta={...save.meta,name:native.meta.name};save.assets.server=actual.project;save.assets.scripts=actual.scripts;
// The simulator's own B template keeps its original index; only the exported GIA carries the editor-assigned one.
if(coverFix)for(const s of save.assets.scripts){const from='local PIXEL_TEMPLATE_INDEX='+indices.PIXEL_TEMPLATE_INDEX+'\n';assert(s.source.includes(from));s.source=s.source.replace(from,'local PIXEL_TEMPLATE_INDEX=1073742822\n');}
for(const s of save.assets.scripts){const hits=[];const walk=n=>{if((n.scriptMappingIds||[]).includes(s.guid))hits.push(n);for(const c of n.children||[])walk(c);};walk(actual.project.root);assert.equal(hits.length,1);s.controlId=hits[0].id;}
fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(save));
const variantNote={menu:'基于050817封面选人恢复版，仅显示诊断文字。',basic:'基于050816基础版（约809个常驻控件，无封面与头像文字池），仅显示诊断文字，用于对照。','menu-deactivate':'基于050817封面选人恢复版，进入战斗加载时对HomeScreen与SelectScreen调用SetActive(false)，返回菜单加载时恢复；用于验证停用隐藏菜单能否消除手机端实例化卡顿。','menu-deactivate-v2':'基于050817封面选人恢复版，修正D3：首次加载时预先缓存全部界面节点；首页与选人页在每次加载期间都停用，加载完成且目标为菜单时才启用（D3回菜单时一开始就启用，销毁战斗图元时菜单仍是激活的）；黑色加载底与全屏背景向左右各多盖半个画布宽，遮住手机两侧露出的3D场景；运行出错时保留全屏背景，错误文字显示在黑底上，不再露出3D场景。诊断行在菜单加载时也显示，行首为D4 MENU或D4 BATTLE。','battle-deactivate-cover':`基于050817封面选人恢复版。放弃D4的“每次加载都停用菜单”：与D3相同，只在战斗加载期间停用首页与选人页。保留的修正有四项：首次加载时预先缓存全部界面节点；菜单加载（进入选人页、每次选角色）期间不再隐藏全屏背景；黑色加载底与全屏背景向左右各多盖半个画布宽；出错时保留背景并显示错误文字。B外层索引已写入为${indices.PIXEL_TEMPLATE_INDEX}，无需手改。`}[variant];
fs.writeFileSync(out+'/说明.md',`# 手机战斗加载诊断 ${tag}\n\n${variantNote}加载顺序、批量与控件数量不变。\n\n双方确认后进度条下方显示：\n\n${tag.slice(0,2)} 阶段 | decode 已解码 left 剩余 | create 已创建/应创建 | task 已完成/总任务 | dt 帧间隔毫秒\n\n阶段依次为 DECODE → CREATE → READY。请录屏，记录CREATE阶段的创建速度、dt与最后数字。\n\n替换双方A为本版，沿用B、GF10与变量，核对B外层索引。\n`);
fs.writeFileSync('work/mobile-load-diagnostic-latest.json',JSON.stringify({out,name,stamp,base,variant}));
console.log(JSON.stringify({out,name,sourceBytes:Buffer.byteLength(lua),giaBytes:a.buffer.length}));
