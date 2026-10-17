import{readFileSync as read,writeFileSync as write}from'node:fs';import assert from'node:assert/strict';
let code=read('work/group1-home-loading.lua','utf8');
function rep(a,b){assert(code.includes(a),'loader missing '+a.slice(0,60));code=code.replace(a,()=>b);}
rep('local loadingPrefabIndex=nil',`local loadingPrefabIndex=nil
resourceGate.loader={view=nil,prefetchKeep={},prefetchQueue={},metrics={}}
function resourceGate.backgroundPrepare()
 local loader=resourceGate.loader;local roles=resourceGate.prefetchRoles and resourceGate.prefetchRoles()or{0,0}
 local key=roles[1]..':'..roles[2]
 if loader.prefetchKey~=key then
  local previous=loader.prefetchKeep
  loader.prefetchKey=key;loader.prefetchKeep={};loader.prefetchQueue={}
  for _,role in ipairs(roles)do if role>0 then for _,frame in ipairs(spriteData[role])do
   if not loader.prefetchKeep[frame]then loader.prefetchKeep[frame]=true;if not frame.rows then loader.prefetchQueue[#loader.prefetchQueue+1]=frame end end
  end end end
  if resourceGate.mode=='menu'then for frame in pairs(previous)do if not loader.prefetchKeep[frame]then frame.rows=nil;frame.raw=nil;frame.decoder=nil;frame.workDone=0 end end end
 end
 local began=loadingNow and loadingNow()or nil
 for n=1,12 do local frame=loader.prefetchQueue[#loader.prefetchQueue];if not frame then break end
  frame.workDone=(frame.workDone or 0)+1;if unpackWork(frame)then table.remove(loader.prefetchQueue)end
 end
end`);
// The helper is before loadingNow; no timing claim for background work. Its fixed cap is conservative.
code=code.replace('local began=loadingNow and loadingNow()or nil','');
rep("loadingTarget=mode;resourceGate.busy=true;", "resourceGate.loader.stats={created=0,destroyed=0,hidden=0,reused=0,decoded=0,updates=0};loadingTarget=mode;resourceGate.busy=true;");
rep("local showHome=mode=='menu'and resourceGate.showHome and resourceGate.showHome()", "local showHome=mode=='menu'and resourceGate.showHome and resourceGate.showHome()\n local view=showHome and'home'or mode=='battle'and'battle'or'select';resourceGate.loader.targetView=view");
rep("for i=1,2 do for _,frame in ipairs(spriteData[choices[i]])do want(frame)end;want(portraitData[choices[i]])end", "for i=1,2 do for _,frame in ipairs(spriteData[choices[i]])do want(frame)end;want(portraitData[choices[i]])end\n  local teams=resourceGate.teamRoles and resourceGate.teamRoles()or{{},{}};for i=1,2 do for n=1,3 do local role=teams[i][n];if role and role>0 then want(thumbData[role])end end end");
rep("frame.rows=nil;frame.decoder=nil;loadingDecode[#loadingDecode+1]=frame;loadingTotal=loadingTotal+unpackCost(frame)", "loadingDecode[#loadingDecode+1]=frame;loadingTotal=loadingTotal+math.max(1,unpackCost(frame)-(frame.workDone or 0))");
rep('else frame.rows=nil;frame.raw=nil;frame.decoder=nil end', "elseif not resourceGate.loader.prefetchKeep[frame]then frame.rows=nil;frame.raw=nil;frame.decoder=nil;frame.workDone=0 end");
rep("if name=='HomeBust1'or name=='HomeBust2'then", "if string.match(name,'^BattleTeam%d%dFace$')then local p,n=string.match(name,'^BattleTeam(%d)(%d)Face$');local teams=resourceGate.teamRoles and resourceGate.teamRoles()or{{},{}};local role=teams[tonumber(p)][tonumber(n)]or 0;wanted=mode=='battle'and role>0 and thumbData[role].count or 0\n  elseif name=='HomeBust1'or name=='HomeBust2'then");
rep('for n=wanted+1,old do loadingUnload[#loadingUnload+1]={j,n,parent}end\n  loadingActive[j]=wanted', `local retain=(mode=='battle'and(name=='Sprite'or name=='Phoenix'))or(mode=='menu'and not showHome and(string.match(name,'^GridFace')or name=='Portrait1'or name=='Portrait2'))
  for n=wanted+1,old do loadingUnload[#loadingUnload+1]={j,n,parent,retain}end
  resourceGate.loader.stats.reused=resourceGate.loader.stats.reused+math.min(old,wanted)
  loadingActive[j]=retain and math.max(old,wanted)or wanted`);
rep("local full=loadingFirst or mode=='battle'", "local full=loadingFirst or view~=resourceGate.loader.view or mode=='battle'");
rep("loadingRegistry[loadingKey(parent)][name]=nil;game.DestroyClientUIControl(loadingInstances[j][n]);loadingInstances[j][n]=nil", `if item[4]then loadingRegistry[loadingKey(parent)][name]:SetVisible(false);resourceGate.loader.stats.hidden=resourceGate.loader.stats.hidden+1
  else loadingRegistry[loadingKey(parent)][name]=nil;game.DestroyClientUIControl(loadingInstances[j][n]);loadingInstances[j][n]=nil;resourceGate.loader.stats.destroyed=resourceGate.loader.stats.destroyed+1 end`);
rep('loadingInstances[j][n]=box', 'loadingInstances[j][n]=box;resourceGate.loader.stats.created=resourceGate.loader.stats.created+1');
rep('local done=unpackWork(frame);loadingDone=', 'local done=unpackWork(frame);frame.workDone=(frame.workDone or 0)+1;resourceGate.loader.stats.decoded=resourceGate.loader.stats.decoded+1;loadingDone=');
rep("if loadingState=='ready'then loadedUpdate(dt);return end", "if loadingState=='ready'then loadedUpdate(dt);if loadingState=='ready'then resourceGate.backgroundPrepare()end;return end");
rep('loadingDraw(dt);if loadingState', 'resourceGate.loader.stats.updates=resourceGate.loader.stats.updates+1;loadingDraw(dt);if loadingState');
rep("local batch=#loadingDecode>0 and 128 or 24", "local batch=#loadingDecode>0 and 128 or(#loadingUnload>0 and 64 or 24)");
rep("loadingState='ready';loadingOverlay:SetVisible(false);menuDraw()", `resourceGate.loader.view=resourceGate.loader.targetView;resourceGate.loader.metrics[#resourceGate.loader.metrics+1]=resourceGate.loader.stats
   local s=resourceGate.loader.stats;print('[LOAD METRIC] '..loadingTarget..' create='..s.created..' destroy='..s.destroyed..' reuse='..s.reused..' decode='..s.decoded..' updates='..s.updates)
   if #resourceGate.loader.metrics>32 then table.remove(resourceGate.loader.metrics,1)end
   loadingState='ready';loadingOverlay:SetVisible(false);menuDraw()`);
rep("if showHome then for _,frame in ipairs(resourceGate.homePortraitData)do want(frame)end end", "if showHome then for _,frame in ipairs(resourceGate.homePortraitData)do want(frame)end end\n if mode=='battle'and resourceGate.stageFrame then want(resourceGate.stageFrame())end");
rep('for _,frame in ipairs(resourceGate.homePortraitData)do visit(frame)end', 'for _,frame in ipairs(resourceGate.homePortraitData)do visit(frame)end\n for _,frame in ipairs(Collision.stageData)do visit(frame)end');
rep("if string.match(name,'^BattleTeam%d%dFace$')then", "if name=='CountryStage'then wanted=mode=='battle'and resourceGate.stageFrame().count or 0\n  elseif string.match(name,'^BattleTeam%d%dFace$')then");
rep("(name=='Sprite'or name=='Phoenix')", "(name=='Sprite'or name=='Phoenix'or name=='CountryStage')");
rep('loadingBar:SetSizeDelta(math.max(1,760*ratio),8);loadingBar:SetAnchoredPosition(-380+380*ratio,-285)', "local cw,ch=game.GetUICanvasSize();local width=math.min(760,cw*.7);local y=-ch/2+135\n loadingOverlay:FindChild('LoadingTrack'):SetAnchoredPosition(0,y);loadingOverlay:FindChild('LoadingTrack'):SetSizeDelta(width,8)\n loadingLabel:SetAnchoredPosition(0,y-35);loadingLabel:SetSizeDelta(cw*.9,56)\n loadingBar:SetSizeDelta(math.max(1,width*ratio),8);loadingBar:SetAnchoredPosition(-width/2+width*ratio/2,y)");
rep('loadingMascot:SetAnchoredPosition(-380+760*ratio,-241+math.sin(loadingClock*5)*6)', 'loadingMascot:SetAnchoredPosition(-width/2+width*ratio,y+44+math.sin(loadingClock*5)*6)');
rep('updates=0};loadingTarget=', 'updates=0,painted=0};resourceGate.loader.stagePaint=nil;loadingTarget=');
rep('loadingTotal=loadingTotal+#loadingQueue+#loadingUnload', `if mode=='battle'then local frame=resourceGate.stageFrame();local cw,ch=game.GetUICanvasSize();resourceGate.loader.stagePaint={frame=frame,n=1,scale=math.max(cw/frame.w,ch/frame.h),key=Collision.stageId(stage,plannedRound)..':'..cw..':'..ch};Collision.stageNodes={};loadingTotal=loadingTotal+math.ceil(frame.count/32)end
 loadingTotal=loadingTotal+#loadingQueue+#loadingUnload`);
rep('item=table.remove(loadingQueue);if not item then return false end', `item=table.remove(loadingQueue);if not item then
   local paint=resourceGate.loader.stagePaint
   if paint and paint.n<=paint.frame.count then local parent=rootNode('CountryStage');local frame=paint.frame
    for n=paint.n,math.min(paint.frame.count,paint.n+31)do local node=loadingFind(parent,'StagePx'..n);Collision.stageNodes[n]=node;local x,y,w,h,color=framePixel(frame,n);node:SetAnchoredPosition((x+w/2-frame.anchor[1])*paint.scale,(frame.anchor[2]-y-h/2)*paint.scale);node:SetSizeDelta(w*paint.scale,h*paint.scale);node.imageColor=color;node:SetVisible(true);resourceGate.loader.stats.painted=resourceGate.loader.stats.painted+1 end
    paint.n=paint.n+32;loadingDone=loadingDone+1;return true
   end
   if paint then Collision.stagePaintKey=paint.key end
   return false end`);
rep("local batch=#loadingDecode>0 and 128 or(#loadingUnload>0 and 64 or 24)", "local device=game.GetDevice();local mobile=device==Enum.Device.Mobile or device==Enum.Device.MobileController\n  local batch=#loadingDecode>0 and 128 or(#loadingUnload>0 and 128 or(mobile and 48 or 96))");
rep('now-began>=.002', 'now-began>=.004');
write('work/repair-loading.lua',code);console.log('REPAIR_LOADER_READY');

