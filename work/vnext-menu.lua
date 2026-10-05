-- Local menu presentation; preparation snapshots are exchanged before simulation.
local menuMode='home'
local menuReady={false,false}
local menuEpoch=1
local menuRevision=0
local menuSeen={-1,-1}
local menuTime=0
local menuDrawKey=''
local debugPanel=false
local portraitNodes,portraitRole={},{}
local function drawPortrait(i,role)
 if portraitRole[i]==role then return end
 local data=portraitData[role];local pool=rootNode('Portrait'..i);portraitNodes[i]=portraitNodes[i]or{}
 for n=1,portraitPool do
  local node=portraitNodes[i][n];if not node then node=pool:FindChild('FacePx'..n);portraitNodes[i][n]=node end
  local r=data.rows[n];node:SetVisible(r~=nil)
  if r then node:SetAnchoredPosition((r[1]+r[3]/2-data.anchor[1])*data.scale,(data.anchor[2]-r[2]-r[4]/2)*data.scale);node:SetSizeDelta(r[3]*data.scale,r[4]*data.scale);node.imageColor=r[5]end
 end
 portraitRole[i]=role
end
local roundIntro=90
local function sendSelection()
 if seat~=1 and seat~=2 then return end
 local s=game.ServerSignal('FighterSelect')
 s:AddInt(seat);s:AddInt(roleChoice[seat]);s:AddInt(menuReady[seat] and 1 or 0)
 s:AddInt(stage);s:AddInt(menuEpoch);s:AddInt(menuRevision);s:SendSignal()
end
local function leaveMatch(destination)
 menuEpoch=menuEpoch+1;menuRevision=menuRevision+1;menuSeen={-1,-1}
 menuReady={false,false};onlineReady=false;joined=false;rb=nil
 menuMode=destination or 'select';menuDrawKey='';sendSelection()
end
local function chooseRole(role)
 if menuMode~='select' or (seat~=1 and seat~=2)then return end
 roleChoice[seat]=role;menuReady[seat]=false;menuRevision=menuRevision+1;sendSelection()
end
local function chooseStage(value)
 if menuMode~='select' or seat~=1 then return end
 stage=value;menuReady={false,false};menuRevision=menuRevision+1;sendSelection()
end
local function setReady()
 if menuMode~='select' or (seat~=1 and seat~=2)then return end
 menuReady[seat]=not menuReady[seat];menuRevision=menuRevision+1;sendSelection()
end
local function menuBind(name,callback)
 rootNode(name):AddCursorEventListener(Enum.CursorEventType.CursorClick,callback)
end
local function menuStart()
 script:RegisterServerSignalHandler('FighterSelectOut',function(_,p)
  local who,role,flag,map,epoch,revision=tonumber(p[1]),tonumber(p[2]),tonumber(p[3]),tonumber(p[4]),tonumber(p[5]),tonumber(p[6])
  if (who~=1 and who~=2)or(role~=1 and role~=2)or(flag~=0 and flag~=1)or not map or map<1 or map>3 or map~=math.floor(map)or not epoch or epoch<1 or epoch~=math.floor(epoch)or not revision or revision<0 or revision~=math.floor(revision)then return end
  if epoch<menuEpoch or who==seat then return end
  if epoch>menuEpoch then
   menuEpoch=epoch;menuReady={false,false};menuSeen={-1,-1};menuRevision=menuRevision+1
   onlineReady=false;joined=false;rb=nil;menuMode='select';menuDrawKey='';sendSelection()
  end
  if revision<=menuSeen[who] then return end
  menuSeen[who]=revision
  if who==1 and stage~=map then stage=map;menuReady[2]=false end
  roleChoice[who]=role;menuReady[who]=flag==1 and map==stage
 end)
 menuBind('StartDuel',function()menuMode='select';menuRevision=menuRevision+1;sendSelection()end)
 menuBind('ChooseKeqing',function()chooseRole(1)end)
 menuBind('ChooseDiluc',function()chooseRole(2)end)
 menuBind('ReadyConfirm',setReady)
 menuBind('BackHome',function()leaveMatch('home')end)
 menuBind('Rematch',function()leaveMatch('select');menuReady[seat]=true;menuRevision=menuRevision+1;sendSelection()end)
 menuBind('Reselect',function()leaveMatch('select')end)
 menuBind('ResultHome',function()leaveMatch('home')end)
 menuBind('DebugToggle',function()debugPanel=not debugPanel end)
end
local function menuDraw()
 local result=onlineReady and(wins[1]>=2 or wins[2]>=2)
 rootNode('HomeScreen'):SetVisible(menuMode=='home')
 rootNode('SelectScreen'):SetVisible(menuMode=='select')
 rootNode('ResultScreen'):SetVisible(menuMode=='battle' and result)
 local selecting=menuMode=='select'
 local fighting=menuMode=='battle'
 for _,name in ipairs({'Light','Heavy','Jump','Block','Restart','Skill','Ultimate','Help','MotionHelp','Stats','Timer','Status','TopPanel','Meter1','Meter2','MeterBack1','MeterBack2','Energy1','Energy2','Name1','Name2','Hp1','Hp2','HpBack1','HpBack2','Combo1','Combo2','State1','State2'})do
  local node=rootNode(name);if node then node:SetVisible(fighting)end
 end
 for d=1,9 do rootNode('Stick'..d):SetVisible(fighting)end
 rootNode('MotionHelp'):SetVisible(false)
 rootNode('Stats'):SetVisible(fighting and debugPanel)
 rootNode('BootDiagnostic'):SetVisible(fighting and debugPanel)
 rootNode('DebugToggle'):SetVisible(fighting)
 rootNode('Restart'):SetVisible(false)
 if phase=='intro' then status.text='' end
 for n=1,3 do rootNode('SelectStage'..n):SetVisible(selecting)end
 rootNode('RoleKeqing'):SetVisible(false);rootNode('RoleDiluc'):SetVisible(false)
 local names={'刻晴','迪卢克'}
 for i=1,2 do
  actors[i]:SetVisible(selecting or fighting)
  rootNode('Shadow'..i):SetVisible(fighting)
  if selecting then
   f[i].role=roleChoice[i];f[i].attack=nil;f[i].down=0;f[i].wake=0;f[i].stun=0;f[i].launched=false;f[i].crouch=false;f[i].block=false;f[i].y=0;f[i].face=i==1 and 1 or -1
   updateSprite(i);actors[i]:SetAnchoredPosition(i==1 and -310 or 310,-92)
   actorNode(i,'Art'):SetLocalScale(f[i].face*1.1,1.1,1);actorNode(i,'Art'):SetLocalRotation(0,0,0)
   actorNode(i,'Art'):SetAnchoredPosition(0,math.sin(menuTime*2)*1.2)
   actorNode(i,'SpecialFx'):SetVisible(false);actorNode(i,'GuardVisual'):SetVisible(false);actorNode(i,'Flash'):SetVisible(false)
   rootNode('SelectName'..i).text='P'..i..'  '..names[roleChoice[i]]
   rootNode('SelectReady'..i).text=menuReady[i] and '已确认' or '选择角色 · 尚未准备'
  end
  local portrait=rootNode('Portrait'..i);portrait:SetVisible(selecting or fighting)
  portrait:SetAnchoredPosition(selecting and(i==1 and -460 or 460)or(i==1 and -598 or 598),selecting and 225 or 285)
  drawPortrait(i,roleChoice[i])
  for n=1,2 do rootNode('Win'..i..n):SetVisible(fighting and wins[i]>=n)end
 end
 rootNode('SelectionHint').text=seat==0 and '等待席位回包…' or('你是 P'..seat..' · '..(seat==1 and '可选择场景' or '场景由 P1 选择'))
 rootNode('ReadyConfirmText').text=(seat>0 and menuReady[seat])and '取消准备' or '确认准备'
 rootNode('RoundBanner'):SetVisible(fighting and phase=='intro')
 rootNode('RoundBanner').text=roundIntro<=25 and 'FIGHT' or({'ROUND ONE','ROUND TWO','FINAL ROUND'})[math.min(round,3)]
 rootNode('ResultTitle').text=(wins[1]>=2 and 'P1' or 'P2')..'  获胜'
 rootNode('ResultScore').text=wins[1]..' : '..wins[2]..' · 三局两胜'
end
