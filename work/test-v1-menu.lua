-- Preparation snapshots: Ready=0 choosing, 1 confirmed/loading, 2 loaded.
local menuMode='home'
local menuReady,menuLoaded={false,false},{false,false}
local menuRevision,menuSeen,menuTime=0,{-1,-1},0
local debugPanel,commandOpen=false,false
local portraitNodes,portraitRole={},{}
local flowChoice,flowSeen,flowRevision={0,0},{-1,-1},0
local function drawPortrait(i,role)
 if portraitRole[i]==role then return end
 local data=portraitData[role];local pool=rootNode('Portrait'..i);portraitNodes[i]=portraitNodes[i]or{}
 for n=1,portraitPool do
  local node=portraitNodes[i][n];if not node then node=loadingFind(pool,'FacePx'..n);portraitNodes[i][n]=node end
  local r=data.rows[n];node:SetVisible(r~=nil)
  if r then node:SetAnchoredPosition((r[1]+r[3]/2-data.anchor[1])*data.scale,(data.anchor[2]-r[2]-r[4]/2)*data.scale);node:SetSizeDelta(r[3]*data.scale,r[4]*data.scale);node.imageColor=r[5]end
 end
 portraitRole[i]=role
end
local function sendSelection()
 if seat~=1 and seat~=2 then return end
 local s=game.ServerSignal('FighterSelect');s:AddInt(seat);s:AddInt(roleChoice[seat])
 s:AddInt(menuMode=='home'and 3 or(menuLoaded[seat]and 2 or(menuReady[seat]and 1 or 0)));s:AddInt(stage);s:AddInt(menuEpoch);s:AddInt(menuRevision);s:SendSignal()
end
local function leaveMatch(destination,targetEpoch)
 menuEpoch=targetEpoch and math.max(menuEpoch,targetEpoch)or(menuEpoch+1);menuRevision=menuRevision+1;menuSeen={-1,-1}
 menuReady={false,false};menuLoaded={false,false};onlineReady=false;joined=false;rb=nil;flowChoice={0,0};flowSeen={-1,-1}
 menuMode=destination or'select';commandOpen=false
 resourceGate.request('menu',roleChoice)
 sendSelection()
end
local function chooseRole(role)
 if menuMode~='select' or resourceGate.busy or menuReady[seat]or(seat~=1 and seat~=2)then return end
 roleChoice[seat]=role;menuRevision=menuRevision+1;sendSelection()
end
local function chooseStage(value)
 if menuMode~='select' or seat~=1 or menuReady[1]or menuReady[2]then return end
 stage=value;menuRevision=menuRevision+1;sendSelection()
end
local function setReady()
 if menuMode~='select' or resourceGate.busy or(seat~=1 and seat~=2)then return end
 menuReady[seat]=not menuReady[seat];menuLoaded[seat]=false;menuRevision=menuRevision+1;sendSelection()
end
local function sendFlow(action)
 if seat<1 then return end
 flowRevision=flowRevision+1;flowChoice[seat]=action
 local s=game.ServerSignal('FighterFlow');s:AddInt(seat);s:AddInt(action);s:AddInt(menuEpoch);s:AddInt(flowRevision);s:SendSignal()
 if action==2 then leaveMatch('select')elseif action==3 then leaveMatch('home')end
end
local function retryFlow()
 if seat>0 and flowChoice[seat]==1 then
  local s=game.ServerSignal('FighterFlow');s:AddInt(seat);s:AddInt(1);s:AddInt(menuEpoch);s:AddInt(flowRevision);s:SendSignal()
 end
end
local function menuBind(name,callback)
 rootNode(name):AddCursorEventListener(Enum.CursorEventType.CursorClick,callback)
end
local function menuStart()
 script:RegisterServerSignalHandler('FighterSelectOut',function(_,p)
  local who,role,flag,map,epoch,revision=tonumber(p[1]),tonumber(p[2]),tonumber(p[3]),tonumber(p[4]),tonumber(p[5]),tonumber(p[6])
  if(who~=1 and who~=2)or not role or role<1 or role>__ROLE_COUNT__ or role~=math.floor(role)or not flag or flag<0 or flag>3 or flag~=math.floor(flag)or not map or map<1 or map>3 or map~=math.floor(map)or not epoch or epoch<1 or epoch~=math.floor(epoch)or not revision or revision<0 then return end
  if epoch<menuEpoch or who==seat then return end
  if epoch>menuEpoch then
   local rematching=flag==2 and flowChoice[seat]==1 and resourceGate.mode=='battle'
   menuEpoch=epoch;menuReady={false,false};menuLoaded={false,false};menuSeen={-1,-1};menuRevision=menuRevision+1
   onlineReady=false;joined=false;rb=nil;menuMode=flag==3 and'home'or'select';flowChoice={0,0}
   if rematching then menuReady={true,true};menuLoaded={true,true}else resourceGate.request('menu',roleChoice)end
   sendSelection()
  end
  if revision<=menuSeen[who]then return end
  menuSeen[who]=revision
  if who==1 and stage~=map then stage=map;menuReady[2]=false;menuLoaded[2]=false end
  roleChoice[who]=role;menuReady[who]=(flag==1 or flag==2)and map==stage;menuLoaded[who]=flag==2 and map==stage
  if flag==0 and resourceGate.mode=='battle'and not onlineReady then menuReady[seat]=false;menuLoaded={false,false};resourceGate.request('menu',roleChoice)end
 end)
 script:RegisterServerSignalHandler('FighterFlowOut',function(_,p)
  local who,action,epoch,revision=tonumber(p[1]),tonumber(p[2]),tonumber(p[3]),tonumber(p[4])
  if(who~=1 and who~=2)or who==seat or not epoch or (action==1 and epoch~=menuEpoch)or(action~=1 and(epoch<menuEpoch-1 or epoch>menuEpoch))or not revision or revision<=flowSeen[who]or(action~=1 and action~=2 and action~=3)then return end
  flowSeen[who]=revision;flowChoice[who]=action
  if action==2 or action==3 then leaveMatch(action==2 and'select'or'home',epoch+1)end
 end)
 menuBind('StartDuel',function()menuMode='select';menuRevision=menuRevision+1;sendSelection()end)
 for role=1,__ROLE_COUNT__ do local r=role;menuBind('ChooseRole'..r,function()chooseRole(r)end)end
 menuBind('ReadyConfirm',setReady);menuBind('BackHome',function()sendFlow(3)end)
 menuBind('Rematch',function()sendFlow(1)end);menuBind('Reselect',function()sendFlow(2)end);menuBind('ResultHome',function()sendFlow(3)end)
 menuBind('DebugToggle',function()debugPanel=not debugPanel end)
 menuBind('CommandToggle',function()commandOpen=not commandOpen end);menuBind('CommandClose',function()commandOpen=false end)
 menuBind('ExitMatch',function()sendFlow(3)end)
 resourceGate.completed=function(mode)
  spriteCache={};visualNodes={};visualValues={};visualCounts={};fxNodes={};fxPose={}
  if mode=='battle' then menuLoaded[seat]=true;menuRevision=menuRevision+1;sendSelection()end
 end
end
local function menuDraw()
 if resourceGate.busy then return end
 if menuMode=='select' and menuReady[1]and menuReady[2]and not menuLoaded[seat]and resourceGate.mode~='battle'then resourceGate.request('battle',roleChoice);return end
 if flowChoice[1]==1 and flowChoice[2]==1 then
  -- A rematch keeps the same assets but starts a fresh network epoch on both peers.
  menuEpoch=menuEpoch+1;flowChoice={0,0};flowSeen={-1,-1};menuSeen={-1,-1};menuRevision=menuRevision+1
  menuReady={true,true};menuLoaded={true,true};onlineReady=false;joined=false;rb=nil;menuMode='select';sendSelection()
 end
 local result=onlineReady and(wins[1]>=2 or wins[2]>=2)
 local selecting=menuMode=='select';local fighting=menuMode=='battle'
 local device=game.GetDevice();local touch=device==Enum.Device.Mobile or device==Enum.Device.MobileController
 rootNode('HomeScreen'):SetVisible(menuMode=='home');rootNode('SelectScreen'):SetVisible(selecting)
 rootNode('ResultScreen'):SetVisible(fighting and result)
 for _,name in ipairs({'Stats','Timer','Status','TopPanel','Meter1','Meter2','MeterBack1','MeterBack2','Energy1','Energy2','Name1','Name2','Hp1','Hp2','HpBack1','HpBack2','Combo1','Combo2','State1','State2'})do rootNode(name):SetVisible(fighting)end
 for _,name in ipairs({'Light','Heavy','Jump','Block','Skill','Ultimate','StickBase'})do rootNode(name):SetVisible(fighting and not result and touch and not commandOpen)end
 for d=1,9 do rootNode('Stick'..d):SetVisible(fighting and not result and touch and not commandOpen)end
 rootNode('Help'):SetVisible(false);rootNode('MotionHelp'):SetVisible(false);rootNode('Restart'):SetVisible(false)
 rootNode('Stats'):SetVisible(fighting and debugPanel);rootNode('BootDiagnostic'):SetVisible(debugPanel);rootNode('DebugToggle'):SetVisible(fighting)
 rootNode('CommandToggle'):SetVisible(fighting);rootNode('ExitMatch'):SetVisible(fighting)
 rootNode('CommandScreen'):SetVisible(commandOpen)
 local r=roleChoice[seat>0 and seat or 1]
 rootNode('CommandTitle').text=roleNames[r]..' · 指令表'
 local s=moveNames[r]
 rootNode('CommandBody').text='A / D  移动     S  蹲伏     空格  跳跃\nJ  轻攻击     K  重攻击     L  防御\nS + J  下段     前 + K  上段     S + K  升空\nE  '..s.special..'\nQ  '..s.super..' · 100 能量\n下前 + J / K  特殊技（可选搓招）\n下前下前 + K  必杀（可选搓招）\nH  关闭指令表 · 联机战斗继续运行'
 if phase=='intro'then status.text=''end
 for n=1,3 do rootNode('SelectStage'..n):SetVisible(selecting);rootNode('Stage'..n):SetVisible(fighting and stage==n)end
 rootNode('StageTitle'):SetVisible(fighting);rootNode('StageTitle').text=({'风起地 · 大树前','蒙德 · 城门大桥','风龙废墟 · 遗迹平台'})[stage]
 rootNode('RoleKeqing'):SetVisible(false);rootNode('RoleDiluc'):SetVisible(false)
 for i=1,2 do
  actors[i]:SetVisible(selecting or fighting);rootNode('Shadow'..i):SetVisible(fighting)
  if selecting then
   f[i].role=roleChoice[i];f[i].attack=nil;f[i].down=0;f[i].wake=0;f[i].stun=0;f[i].launched=false;f[i].crouch=false;f[i].block=false;f[i].y=0;f[i].face=i==1 and 1 or -1
   updateSprite(i);actors[i]:SetAnchoredPosition(i==1 and -310 or 310,-70)
   actorNode(i,'Art'):SetLocalScale(f[i].face,1,1);actorNode(i,'Art'):SetLocalRotation(0,0,0);actorNode(i,'Art'):SetAnchoredPosition(0,math.sin(menuTime*2)*1.2)
   for _,name in ipairs({'SpecialFx','GuardVisual','Flash','Phoenix','Stiletto','FlameArc'})do actorNode(i,name):SetVisible(false)end
   for n=1,4 do actorNode(i,'BurstLine'..n):SetVisible(false)end
   rootNode('SelectName'..i).text='P'..i..'  '..roleNames[roleChoice[i]]
   rootNode('SelectReady'..i).text=menuLoaded[i]and'加载完成' or(menuReady[i]and'已确认 · 等待双方加载'or'尚未准备')
  end
  local portrait=rootNode('Portrait'..i);portrait:SetVisible(selecting or fighting);portrait:SetAnchoredPosition(selecting and(i==1 and -460 or 460)or(i==1 and -598 or 598),selecting and 225 or 285);drawPortrait(i,roleChoice[i])
  for n=1,2 do rootNode('Win'..i..n):SetVisible(fighting and wins[i]>=n)end
 end
 rootNode('SelectionHint').text=seat==0 and'等待席位回包…'or('你是 P'..seat..' · '..(seat==1 and'场景选择权'or'场景由 P1 选择'))
 rootNode('ReadyConfirmText').text=seat>0 and menuReady[seat]and'取消准备'or'确认准备'
 if selecting then for r=1,__ROLE_COUNT__ do local card=rootNode('ChooseRole'..r);local plate=card:FindChild('ChooseRole'..r..'Plate');plate.imageColor=r==roleChoice[1]and 0xff685382 or(r==roleChoice[2]and 0xff845640 or 0xff233a50)end end
 rootNode('RoundBanner'):SetVisible(fighting and phase=='intro');rootNode('RoundBanner').text=roundIntro<=25 and'FIGHT'or({'ROUND ONE','ROUND TWO','FINAL ROUND'})[math.min(round,3)]
 rootNode('ResultTitle').text=(wins[1]>=2 and'P1'or'P2')..'  获胜'
 rootNode('ResultScore').text=wins[1]..' : '..wins[2]..' · 三局两胜'..((flowChoice[1]==1 or flowChoice[2]==1)and' · 等待双方再战'or'')
end
