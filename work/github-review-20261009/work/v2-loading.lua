-- Compressed tables expand only for this menu page / these two current-round fighters.
local loadedInit,loadedStart,loadedUpdate=OnInit,OnStart,OnUpdate
local loadingRoot,loadingOverlay,loadingBar,loadingLabel,loadingMascot,loadingSeed
local loadingState,loadingClock,loadingPose='wait',0,0
local loadingQueue,loadingUnload,loadingInstances,loadingActive={},{},{},{}
local loadingDecode={}
local loadingDone,loadingTotal,loadingTarget,loadingFirst=0,0,'menu',true
local PIXEL_TEMPLATE_INDEX=1073741845
local loadingPrefabIndex=nil
local function loadingNow()local ok,t=pcall(function()return os.clock()end);return ok and type(t)=='number'and t or nil end
local function loadingDraw(dt)
 loadingClock=loadingClock+dt;local ratio=loadingTotal>0 and math.min(1,loadingDone/loadingTotal)or 1
 loadingBar:SetSizeDelta(math.max(1,760*ratio),8);loadingBar:SetAnchoredPosition(-380+380*ratio,-285)
 loadingMascot:SetAnchoredPosition(-380+760*ratio,-241+math.sin(loadingClock*5)*6)
 local pose=math.floor(loadingClock*7)%#loadingPaimonFrames+1
 if pose~=loadingPose then loadingPose=pose;local frame=loadingPaimonFrames[pose]
  for n=1,#loadingMascot:GetChildren()do local node=loadingMascot:FindChild('M'..n);local r=frame.rows[n]
   node:SetVisible(r~=nil);if r then node:SetAnchoredPosition((r[1]+r[3]/2-frame.anchor[1])*frame.scale,(frame.anchor[2]-r[2]-r[4]/2)*frame.scale);node:SetSizeDelta(r[3]*frame.scale,r[4]*frame.scale);node.imageColor=Color.FromRGBA(r[5],r[6],r[7],r[8])end
  end
 end
 if loadingState~='error'then loadingLabel.text=(loadingTarget=='battle'and'准备本回合角色'or'准备当前页头像 / 回收素材')..'  '..math.floor(ratio*100)..'% · '..loadingDone..' / '..loadingTotal end
end
local function loadingRequest(mode,choices)
 if resourceGate.busy and loadingState~='wait'then resourceGate.pending={mode,{choices[1],choices[2]}};return end
 loadingTarget=mode;resourceGate.busy=true;loadingState='paint';loadingDone=0;loadingTotal=0;loadingQueue={};loadingUnload={};loadingDecode={}
 local previews,page={0,0},1;if resourceGate.menuRoles then previews,page=resourceGate.menuRoles()end
 local desired,seen={},{}
 local function want(frame)if frame then desired[frame]=true end end
 if mode=='battle'then
  for i=1,2 do for _,frame in ipairs(spriteData[choices[i]])do want(frame)end;want(portraitData[choices[i]])end
 else
  for n=1,10 do want(thumbData[(page-1)*10+n])end
  for i=1,2 do if previews[i]>0 then want(portraitData[previews[i]])end end
 end
 local function visit(frame)
  if seen[frame]then return end;seen[frame]=true
  if desired[frame]then if not frame.rows or frame.decoder then frame.rows=nil;frame.decoder=nil;loadingDecode[#loadingDecode+1]=frame;loadingTotal=loadingTotal+unpackCost(frame)end
  else frame.rows=nil;frame.raw=nil;frame.decoder=nil end
 end
 for _,frames in ipairs(spriteData)do for _,frame in ipairs(frames)do visit(frame)end end
 for _,frames in ipairs({portraitData,thumbData})do for _,frame in ipairs(frames)do visit(frame)end end
 local caps={mode=='battle'and poolCaps[choices[1]]or 0,mode=='battle'and poolCaps[choices[2]]or 0};resourceGate.caps=caps
 for j,job in ipairs(loadingJobs)do
  local parent=loadingRoot;for _,name in ipairs(job.path)do parent=parent:FindChild(name)end
  local name=parent.name;local who=job.path[1]=='Keqing'and 1 or 2;local wanted=0
  if name=='Sprite'then wanted=caps[who]
  elseif name=='Phoenix'then wanted=mode=='battle'and choices[who]==2 and #job.rows or 0
  elseif name=='Portrait1'or name=='Portrait2'then local i=name=='Portrait1'and 1 or 2;local role=mode=='battle'and choices[i]or previews[i];wanted=role>0 and portraitData[role].count or 0
  elseif string.match(name,'^GridFace%d+$')then local n=tonumber(string.match(name,'%d+'));local role=(page-1)*10+n;wanted=mode=='menu'and thumbData[role]and thumbData[role].count or 0
  end
  local old=loadingActive[j]or 0;loadingInstances[j]=loadingInstances[j]or{}
  for n=old+1,wanted do loadingQueue[#loadingQueue+1]={j,n,parent}end
  for n=wanted+1,old do loadingUnload[#loadingUnload+1]={j,n,parent}end
  loadingActive[j]=wanted
 end
 loadingTotal=loadingTotal+#loadingQueue+#loadingUnload
 local full=loadingFirst or mode=='battle'
 if full then for _,node in ipairs(loadingRoot:GetChildren())do if node.name~='LoadingScreen'and node.name~='LoadingPixelTemplate'then node:SetVisible(false)end end end
 loadingOverlay:SetVisible(true);loadingOverlay:FindChild('LoadingBlack'):SetVisible(full);loadingOverlay:SetAsFirstSibling();loadingDraw(0)
 print('[RESOURCE] '..mode..' compressed tasks='..loadingTotal..' current sprite caps='..caps[1]..','..caps[2])
end
local function loadingWork()
 if #loadingDecode>0 then local frame=loadingDecode[#loadingDecode];local done=unpackWork(frame);loadingDone=loadingDone+1;if done then table.remove(loadingDecode)end;return true end
 local item=table.remove(loadingUnload)
 if item then local j,n,parent=item[1],item[2],item[3];local row=loadingJobs[j].rows[n];loadingRegistry[loadingKey(parent)][row[1]]=nil;game.DestroyClientUIControl(loadingInstances[j][n]);loadingInstances[j][n]=nil
 else
  item=table.remove(loadingQueue);if not item then return false end
  local j,n,parent=item[1],item[2],item[3];local row=loadingJobs[j].rows[n]
  if not loadingPrefabIndex then loadingPrefabIndex=PIXEL_TEMPLATE_INDEX>0 and PIXEL_TEMPLATE_INDEX or loadingSeed.referencedPrefabIndex end
  local box=game.InstantiateClientUIControl(loadingPrefabIndex,parent);if not box then error('无法创建图元：请检查 B 模板索引 '..tostring(loadingPrefabIndex))end
  if parent.name=='Portrait1'or parent.name=='Portrait2'then box:SetAsLastSibling()end
  local pixel=box:FindChild('Pixel');if not pixel then error('B 模板缺少 Pixel')end;pixel.name=row[1];pixel:SetVisible(false)
  local key=loadingKey(parent);loadingRegistry[key]=loadingRegistry[key]or{};loadingRegistry[key][row[1]]=pixel;loadingInstances[j][n]=box
 end
 loadingDone=loadingDone+1;return true
end
function OnInit()
 loadingRoot=script.object;loadingOverlay=loadingRoot:FindChild('LoadingScreen');loadingBar=loadingOverlay:FindChild('LoadingBar');loadingLabel=loadingOverlay:FindChild('LoadingText');loadingMascot=loadingOverlay:FindChild('LoadingPaimon');loadingSeed=loadingRoot:FindChild('LoadingPixelTemplate')
 resourceGate.request=loadingRequest;loadingRequest('menu',{1,2})
end
function OnStart()script:EnableUpdate(true)end
function OnUpdate(dt)
 if loadingState=='ready'then loadedUpdate(dt);return end
 local ok,message=pcall(function()
  loadingDraw(dt);if loadingState=='error'then return end
  if loadingState=='paint'then loadingState='create';return end
  local began=loadingNow();local batch=#loadingDecode>0 and 128 or 24
  for n=1,batch do if not loadingWork()then loadingState='complete';break end;local now=loadingNow();if began and now and now-began>=.002 then break end end
  if loadingState=='complete'then
   resourceGate.mode=loadingTarget;resourceGate.busy=false
   if loadingFirst then loadingFirst=false;loadedInit();loadedStart();local diagnostic=loadingRoot:FindChild('BootDiagnostic');if diagnostic and string.find(diagnostic.text,'ERROR')then error(diagnostic.text)end end
   if resourceGate.pending then local p=resourceGate.pending;resourceGate.pending=nil;loadingState='wait';loadingRequest(p[1],p[2]);return end
   if resourceGate.completed then resourceGate.completed(loadingTarget)end
   loadingState='ready';loadingOverlay:SetVisible(false);menuDraw()
  end
 end)
 if not ok then loadingState='error';loadingLabel.text='加载失败：'..tostring(message);print('[RESOURCE ERROR] '..tostring(message))end
end
