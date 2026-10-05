-- Run the original lifecycle only after all real creation jobs complete.
local loadedInit,loadedStart,loadedUpdate=OnInit,OnStart,OnUpdate
local loadingRoot,loadingOverlay,loadingBar,loadingLabel,loadingMascot,loadingSeed
local loadingState='wait'
local loadingGroup,loadingRow,loadingDone,loadingTotal,loadingClock=1,1,0,0,0
local loadingRestore={}
local loadingParent=nil
local loadingPose=0
local CREATE_BATCH=32
local WORK_BUDGET=.004
-- Optional: enter the actual imported CLIENT TEMPLATE CONTAINER index here.
-- Leave zero when LoadingPixelTemplate reference is correctly bound.
local PIXEL_TEMPLATE_INDEX=1073741845 -- User's imported B container; update if reimport changes it.
local loadingPrefabIndex=nil
local loadingUpdates=0
local function loadingNow()
 local ok,t=pcall(function()return os.clock()end)
 return ok and type(t)=='number' and t or nil
end
local function loadingDraw(dt)
 loadingClock=loadingClock+dt
 local ratio=loadingTotal>0 and loadingDone/loadingTotal or 0
 loadingBar:SetSizeDelta(math.max(1,760*ratio),8)
 loadingBar:SetAnchoredPosition(-380+380*ratio,-285)
 loadingMascot:SetAnchoredPosition(-380+760*ratio,-241+math.sin(loadingClock*5)*6)
 local pose=math.floor(loadingClock*7)%#loadingPaimonFrames+1
 if pose~=loadingPose then
  loadingPose=pose;local frame=loadingPaimonFrames[pose]
  for n=1,#loadingMascot:GetChildren()do
   local control=loadingMascot:FindChild('M'..n);local r=frame.rows[n]
   if r then
    control:SetAnchoredPosition((r[1]+r[3]/2-frame.anchor[1])*frame.scale,(frame.anchor[2]-r[2]-r[4]/2)*frame.scale)
    control:SetSizeDelta(r[3]*frame.scale,r[4]*frame.scale)
    control.imageColor=Color.FromRGBA(r[5],r[6],r[7],r[8]);control:SetVisible(true)
   else control:SetVisible(false)end
  end
 end
 if loadingState~='error' then loadingLabel.text='正在加载 '..math.floor(ratio*100)..'%  ·  '..loadingDone..' / '..loadingTotal end
end
local function initializeLoading()
 loadingRoot=script.object
 loadingOverlay=loadingRoot:FindChild('LoadingScreen');loadingBar=loadingOverlay:FindChild('LoadingBar')
 loadingLabel=loadingOverlay:FindChild('LoadingText');loadingMascot=loadingOverlay:FindChild('LoadingPaimon')
 loadingSeed=loadingRoot:FindChild('LoadingPixelTemplate')
 for _,c in ipairs(loadingRoot:GetChildren())do
  if c.name~='LoadingScreen' and c.name~='LoadingPixelTemplate' then loadingRestore[#loadingRestore+1]={c,c.visible};c:SetVisible(false)end
 end
 loadingOverlay:SetVisible(true);loadingOverlay:SetAsFirstSibling()
 for _,job in ipairs(loadingJobs)do loadingTotal=loadingTotal+#job.rows end
 loadingState='paint';loadingDraw(0)
end
local function loadingFail(stage,message)
 loadingState='error'
 if loadingLabel then loadingLabel.text=stage..'失败：'..tostring(message);loadingLabel:SetVisible(true)end
 print('[LOAD] '..stage..' ERROR '..tostring(message))
end
function OnInit()
 local ok,message=pcall(initializeLoading)
 if not ok then loadingFail('初始化',message)
 elseif loadingLabel then loadingLabel.text='Lua 已初始化，等待 OnStart' end
end
function OnStart()
 local ok,message=pcall(function()script:EnableUpdate(true)end)
 if not ok then loadingFail('启动',message)
 elseif loadingState~='error' and loadingLabel then loadingLabel.text='Lua 已启动，准备创建图元' end
end
local function loadingCreate()
 if not loadingParent then
  loadingParent=loadingRoot
  for _,name in ipairs(loadingJobs[loadingGroup].path)do loadingParent=loadingParent:FindChild(name);if not loadingParent then error('加载层级不存在 '..name)end end
 end
 local row=loadingJobs[loadingGroup].rows[loadingRow]
 if not loadingPrefabIndex then
  if PIXEL_TEMPLATE_INDEX>0 then loadingPrefabIndex=PIXEL_TEMPLATE_INDEX
  else
   local ok,index=pcall(function()return loadingSeed.referencedPrefabIndex end)
   if not ok or type(index)~='number' or index<=0 then error('未绑定图元模板；将 LoadingPixelTemplate 引用选为 B 模板，或填 Lua 的 PIXEL_TEMPLATE_INDEX')end
   loadingPrefabIndex=index
  end
 end
 local box=game.InstantiateClientUIControl(loadingPrefabIndex,loadingParent)
 if not box then error('图元模板索引 '..loadingPrefabIndex..' 无法创建；请使用客户端模板容器索引')end
 if loadingParent.name=='Portrait1' or loadingParent.name=='Portrait2' then box:SetAsFirstSibling()end
 local pixel=box:FindChild('Pixel');if not pixel then error('加载模板缺少 Pixel')end
 pixel.name=row[1];pixel:SetVisible(false)
 local c=row[6];
 local key=loadingKey(loadingParent);loadingRegistry[key]=loadingRegistry[key]or{};loadingRegistry[key][row[1]]=pixel
 loadingDone=loadingDone+1;loadingRow=loadingRow+1
 if loadingRow>#loadingJobs[loadingGroup].rows then loadingGroup=loadingGroup+1;loadingRow=1;loadingParent=nil end
end
local function updateLoading(dt)
 if loadingState=='ready' then loadedUpdate(dt);return end
 loadingDraw(dt)
 if loadingState=='paint' then loadingState='create';return end
 if loadingState=='error' then return end
 if loadingState=='complete' then
  local ok,message=pcall(function()
   for _,entry in ipairs(loadingRestore)do entry[1]:SetVisible(entry[2])end
   loadedInit();loadedStart()
   local diagnostic=loadingRoot:FindChild('BootDiagnostic')
   if diagnostic and string.find(diagnostic.text,'ERROR:')then error(diagnostic.text)end
  end)
  if not ok then loadingState='error';loadingLabel.text='加载失败：'..tostring(message);return end
  loadingOverlay:SetVisible(false);loadingState='ready';return
 end
 local began=loadingNow()
 for n=1,CREATE_BATCH do
  if loadingDone>=loadingTotal then loadingState='complete';break end
  local ok,message=pcall(loadingCreate)
  if not ok then loadingState='error';loadingLabel.text='加载失败：'..tostring(message);print('[LOAD] '..tostring(message));return end
  local now=loadingNow();if began and now and now-began>=WORK_BUDGET then break end
 end
 loadingDraw(0)
end
function OnUpdate(dt)
 loadingUpdates=loadingUpdates+1
 local ok,message=pcall(updateLoading,dt)
 if not ok then loadingFail('更新',message)end
end
