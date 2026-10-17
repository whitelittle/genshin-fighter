import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {progressOnlyRuntime,progressOnlyControls} from './loading-progress-only.mjs';
import {exportGia,validateServerGiaCompatibility,importGia} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const out='outputs/loading-fix-20261005';fs.mkdirSync(out,{recursive:true});
const delivery=JSON.parse(fs.readFileSync('outputs/full-reinstall/delivery.json'));
const original=JSON.parse(fs.readFileSync('outputs/full-reinstall/simulator.save.json'));
const baselineHashes=Object.fromEntries(delivery.files.map(f=>[f.filename,crypto.createHash('sha256').update(fs.readFileSync('outputs/full-reinstall/'+f.filename)).digest('hex')]));
let source=progressOnlyRuntime(original.assets.scripts[0].source);
function replace(a,b){assert(source.includes(a),'Missing source anchor: '+a.slice(0,100));source=source.replace(a,()=>b);}
replace('local function loadingRequest(mode,choices)',`resourceGate.waitingForBattle=function()return menuMode=='roundload'end
resourceGate.loader.coverVisible=nil
resourceGate.loader.syncCover=function()
 local waiting=loadingState=='ready' and resourceGate.waitingForBattle()
 local show=loadingState~='ready' or waiting
 if show~=resourceGate.loader.coverVisible then
  resourceGate.loader.coverVisible=show;loadingOverlay:SetVisible(show)
  if show then loadingOverlay:SetAsFirstSibling()end
 end
 if waiting then loadingOverlay:FindChild('LoadingBlack'):SetVisible(true);loadingDraw(0)end
end
local function loadingRequest(mode,choices)`);
replace('painted=0};resourceGate.loader.stagePaint=nil',`painted=0,phaseCpu={},phaseTasks={},wallSeconds=0,progressWrites=0,layoutWrites=0};resourceGate.loader.stagePaint=nil`);
replace("loadingDisplayClock=.1;loadingBarWidth=nil;loadingLabel:SetVisible(false);loadingOverlay:SetVisible(true);", "loadingDisplayClock=.1;loadingBarWidth=nil;loadingLabel:SetVisible(false);resourceGate.loader.coverVisible=true;loadingOverlay:SetVisible(true);");
replace("if filled~=loadingBarWidth then", "if filled~=loadingBarWidth then\n  if resourceGate.loader.stats then resourceGate.loader.stats.progressWrites=resourceGate.loader.stats.progressWrites+2 end");
replace('loadingCanvasW=cw;loadingCanvasH=ch;loadingBarWidth=nil',`loadingCanvasW=cw;loadingCanvasH=ch;loadingBarWidth=nil
  if resourceGate.loader.stats then resourceGate.loader.stats.layoutWrites=resourceGate.loader.stats.layoutWrites+4 end`);
replace('local function loadingWork()', 'local function loadingWorkRaw()');
replace('function OnInit()\n loadingRoot=script.object;loadingOverlay=',`local function loadingWork()
 local stats=resourceGate.loader.stats
 local phase=#loadingDecode>0 and 'decode' or(#loadingUnload>0 and 'recycle' or(#loadingQueue>0 and 'create' or 'paint'))
 local began=loadingNow();local worked=loadingWorkRaw();local ended=loadingNow()
 if worked then stats.phaseTasks[phase]=(stats.phaseTasks[phase]or 0)+1 end
 if began and ended then stats.phaseCpu[phase]=(stats.phaseCpu[phase]or 0)+math.max(0,ended-began)end
 return worked
end
function OnInit()
 loadingRoot=script.object;loadingOverlay=`);
replace("if loadingState=='ready'then loadedUpdate(dt);if loadingState=='ready'then resourceGate.backgroundPrepare()end;return end",`if loadingState=='ready'then
  loadedUpdate(dt)
  if loadingState=='ready'then resourceGate.backgroundPrepare()end
  resourceGate.loader.syncCover();return
 end`);
replace('resourceGate.loader.stats.updates=resourceGate.loader.stats.updates+1;loadingDraw(dt);',`resourceGate.loader.stats.updates=resourceGate.loader.stats.updates+1
  resourceGate.loader.stats.wallSeconds=resourceGate.loader.stats.wallSeconds+math.max(0,dt)
  local updateBegan=loadingNow();loadingDraw(dt);`);
replace("local began=loadingNow();local device=game.GetDevice();local mobile=device==Enum.Device.Mobile or device==Enum.Device.MobileController\n  local batch=#loadingDecode>0 and 128 or(#loadingUnload>0 and 128 or(mobile and 48 or 96))\n  for n=1,batch do if not loadingWork()then loadingState='complete';break end;local now=loadingNow();if began and now and now-began>=.004 then break end end",`local began=updateBegan;local device=game.GetDevice();local mobile=device==Enum.Device.Mobile or device==Enum.Device.MobileController
  local ceiling=#loadingDecode>0 and 128 or(#loadingUnload>0 and 128 or(mobile and 48 or 96))
  local loader=resourceGate.loader;loader.batchFactor=loader.batchFactor or 1
  -- Frame interval is a scheduling signal, not CPU/GPU time or measured power.
  if dt>.04 then loader.batchFactor=math.max(.125,loader.batchFactor*.75)
  elseif dt>0 and dt<.022 then loader.batchFactor=math.min(1,loader.batchFactor+.02)end
  local batch=math.max(1,math.floor(ceiling*loader.batchFactor));local budget=mobile and .002 or .004
  for n=1,batch do
   local now=loadingNow();if n>1 and began and now and now-began>=budget then break end
   if not loadingWork()then loadingState='complete';break end
  end
  resourceGate.loader.stats.lastBatch=batch;resourceGate.loader.stats.luaSoftBudget=budget`);
replace("loadingState='ready';loadingOverlay:SetVisible(false);menuDraw()",`loadingState='ready';loadingDisplayClock=.1;loadingDraw(0);menuDraw();resourceGate.loader.syncCover()
   local s=resourceGate.loader.stats
   for _,phase in ipairs({'decode','recycle','create','paint'})do print('[LOAD PHASE] '..phase..' tasks='..(s.phaseTasks[phase]or 0)..' cpu='..(s.phaseCpu[phase]or 0))end
   print('[LOAD SCHEDULE] wall='..s.wallSeconds..' progressWrites='..s.progressWrites..' layoutWrites='..s.layoutWrites..' batch='..(s.lastBatch or 0))`);
replace("if not ok then loadingState='error';loadingLabel:SetVisible(true);loadingLabel.text=", "if not ok then loadingState='error';loadingLabel:SetVisible(true);loadingOverlay:SetVisible(true);loadingOverlay:SetAsFirstSibling();loadingOverlay:FindChild('LoadingBlack'):SetVisible(true);loadingLabel.text=");
// Limit background predecode with the same device-aware soft budget, avoiding unbounded menu work.
replace('for n=1,12 do local frame=loader.prefetchQueue',`local began=loadingNow and loadingNow()or nil
 for n=1,12 do
  local now=loadingNow and loadingNow()or nil;if n>1 and began and now and now-began>=.001 then break end
  local frame=loader.prefetchQueue`);
// backgroundPrepare precedes the local clock declaration: use a loader field instead.
source=source.replaceAll('loadingNow and loadingNow()or nil','loader.clock and loader.clock()or nil');
replace('local function loadingDraw(dt)', 'resourceGate.loader.clock=loadingNow\nlocal function loadingDraw(dt)');
source=source.replace('local loadingCanvasW,loadingCanvasH,loadingBarWidth','').replace('local loadingDisplayClock=0','');
for(const [name,key]of Object.entries({loadingCanvasW:'canvasW',loadingCanvasH:'canvasH',loadingBarWidth:'barWidth',loadingDisplayClock:'displayClock'}))source=source.replaceAll(name,'resourceGate.loader.'+key);
source=source.replace('resourceGate.loader={view=nil,prefetchKeep={},prefetchQueue={},metrics={}}','resourceGate.loader={view=nil,prefetchKeep={},prefetchQueue={},metrics={},displayClock=0}');
const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean);
const sim=structuredClone(original);const removed=progressOnlyControls(sim.assets.server.root);
const backing=structuredClone(find(sim.assets.server.root,'LoadingBlack'));backing.id='fullscreen_backing_20261005';backing.guid=1073900001;backing.name='FullscreenBacking';backing.visible=true;backing.active=true;backing.imageColor=0xff101b2c;backing.children=[];
for(const t of Object.values(backing.transformByPlatform)){t.anchorMin={x:0,y:0};t.anchorMax={x:1,y:1};t.pivot={x:.5,y:.5};t.offset={x:0,y:0};t.size={x:800,y:800};t.scale={x:1,y:1,z:1};}
// Server-root sibling survives every host page hide. Padding tests unclipped safe-area parents;
// a platform clipping its entire canvas still requires real-device diagnosis.
sim.assets.server.root.children[0].children.push(backing);
replace("if node.name~='LoadingScreen'and node.name~='LoadingPixelTemplate'then node:SetVisible(false)end", "if node.name~='LoadingScreen'and node.name~='LoadingPixelTemplate'and node.name~='FullscreenBacking'then node:SetVisible(false)end");
sim.assets.scripts[0].source=source;sim.assets.scripts[0].path='lua/loading_fix_20261005.lua';sim.assets.scripts[0].filename='loading_fix_20261005.lua';
sim.meta.name='加载与显示修复候选 20261005';sim.assets.server.meta.name=sim.meta.name;sim.assets.server.meta.giaFileName='加载与显示修复候选_A.gia';
fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(sim));fs.writeFileSync(out+'/完整游戏.lua',source);
const native=JSON.parse(fs.readFileSync('outputs/full-reinstall/fighter.save.json'));native.assets.server=structuredClone(sim.assets.server);native.assets.scripts=structuredClone(sim.assets.scripts);native.meta=structuredClone(sim.meta);fs.writeFileSync(out+'/fighter.save.json',JSON.stringify(native));
const a=exportGia(native.assets.server,{scripts:native.assets.scripts});assert(validateServerGiaCompatibility(a.buffer).valid);assert(importGia(a.buffer,'加载与显示修复候选_A.gia').scripts.some(s=>s.source===source));fs.writeFileSync(out+'/加载与显示修复候选_A.gia',a.buffer);
for(const [name,hash]of Object.entries(baselineHashes))assert.equal(crypto.createHash('sha256').update(fs.readFileSync('outputs/full-reinstall/'+name)).digest('hex'),hash);
fs.writeFileSync(out+'/build.json',JSON.stringify({baseline:'20261004_210009',baselineHashes,removedPaimonControls:removed,addedBackingControls:1,pixelTemplateIndex:delivery.pixelTemplateIndex,signalBindings:delivery.bindings,newExternalInstall:false,deviceVerified:false,coverageFix:'persistent stretched backing with padding; device clipping remains unverified',scheduler:'adaptive task ceiling; mobile 2ms / PC 4ms Lua soft budget; prefetch 1ms'},null,2));
console.log(JSON.stringify({out,removedPaimonControls:removed,aBytes:a.buffer.length}));
