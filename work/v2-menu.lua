-- R1/R2/R3 are separate rounds, not in-round tag / relay.
local menuMode='home'
local menuReady,menuLoaded={false,false},{false,false}
local menuRevision,menuSeen,menuTime=0,{-1,-1},0
local debugPanel,commandOpen=false,false
local portraitNodes,portraitRole={},{}
local flowChoice,flowSeen,flowRevision={0,0},{-1,-1},0
local teamChoice={{0,0,0},{0,0,0}}
local previewChoice={0,0}
local rosterPage,menuDirty=1,true
local plannedRound,teamScores=1,{0,0}
local gridNodes,gridRoles={},{}
local function plateColor(name,color)
 rootNode(name).imageColor=color;rootNode(name..'Middle').imageColor=color
 for _,sx in ipairs({-1,1})do for _,sy in ipairs({-1,1})do rootNode(name..'Corner'..sx..'_'..sy).imageColor=color end end
end
local function selected(who,role)for n=1,3 do if teamChoice[who][n]==role then return n end end return nil end
local function complete(who)return teamChoice[who][1]>0 and teamChoice[who][2]>0 and teamChoice[who][3]>0 end
local function paintFrame(parent,prefix,data,scale,nodes)
 if not data or not data.rows then return end
 for n=1,data.count do
  local node=nodes[n];if not node then node=loadingFind(parent,prefix..n);nodes[n]=node end
  local x,y,w,h,color=framePixel(data,n);node:SetVisible(true);node:SetAnchoredPosition((x+w/2-data.anchor[1])*scale,(data.anchor[2]-y-h/2)*scale);node:SetSizeDelta(w*scale,h*scale);node.imageColor=color
 end
 for n=data.count+1,#nodes do nodes[n]:SetVisible(false)end
end
local function drawPortrait(i,role)
 if role<=0 then return end
 local key=role..':'..menuMode;if portraitRole[i]==key then return end
 local pool=rootNode('Portrait'..i);portraitNodes[i]=portraitNodes[i]or{}
 paintFrame(pool,'FacePx',portraitData[role],menuMode=='battle'and 1.45 or 2.7,portraitNodes[i]);portraitRole[i]=key
end
local function sendSelection()
 if seat~=1 and seat~=2 then return end
 local s=game.ServerSignal('FighterTeam');s:AddInt(seat)
 for n=1,3 do s:AddInt(teamChoice[seat][n])end
 s:AddInt(menuMode=='home'and 3 or(menuLoaded[seat]and 2 or(menuReady[seat]and 1 or 0)))
 s:AddInt(stage);s:AddInt(menuEpoch);s:AddInt(menuRevision);s:AddInt(plannedRound);s:AddInt(teamScores[1]);s:AddInt(teamScores[2]);s:SendSignal()
end
local function startNetworkRound()
 if plannedRound==1 then restart()else round=plannedRound;wins={teamScores[1],teamScores[2]};tick=0;resetRound()end
 menuDirty=true
end
local function leaveMatch(destination,targetEpoch)
 menuEpoch=targetEpoch and math.max(menuEpoch,targetEpoch)or(menuEpoch+1);menuRevision=menuRevision+1;menuSeen={-1,-1}
 menuReady={false,false};menuLoaded={false,false};onlineReady=false;joined=false;rb=nil;flowChoice={0,0};flowSeen={-1,-1}
 plannedRound=1;teamScores={0,0};teamChoice={{0,0,0},{0,0,0}};previewChoice={0,0}
 menuMode=destination or'select';commandOpen=false;menuDirty=true
 resourceGate.request('menu',roleChoice);sendSelection()
end
local function chooseRole(role)
 if menuMode~='select'or resourceGate.busy or menuReady[seat]or(seat~=1 and seat~=2)then return end
 local at=selected(seat,role)
 if not at and complete(seat)then rootNode('SelectionHint').text='阵容已满：点击已选头像或回合栏位撤回后再选';return end
 if at then for n=at,2 do teamChoice[seat][n]=teamChoice[seat][n+1]end;teamChoice[seat][3]=0
 else for n=1,3 do if teamChoice[seat][n]==0 then teamChoice[seat][n]=role;break end end end
 previewChoice[seat]=at and(teamChoice[seat][3]>0 and teamChoice[seat][3]or(teamChoice[seat][2]>0 and teamChoice[seat][2]or teamChoice[seat][1]))or role;roleChoice[seat]=teamChoice[seat][1]>0 and teamChoice[seat][1]or role
 menuRevision=menuRevision+1;menuDirty=true;sendSelection();resourceGate.request('menu',roleChoice)
end
local function setReady()
 if menuMode~='select'or resourceGate.busy or(seat~=1 and seat~=2)then return end
 if not complete(seat)then rootNode('SelectionHint').text='请先选满三个角色：ROUND 1 → ROUND 2 → ROUND 3';return end
 menuReady[seat]=not menuReady[seat];menuLoaded[seat]=false;menuRevision=menuRevision+1
 roleChoice[seat]=teamChoice[seat][1];menuDirty=true;sendSelection()
end
local function sendFlow(action)
 if seat<1 then return end
 flowRevision=flowRevision+1;flowChoice[seat]=action;menuDirty=true
 local s=game.ServerSignal('FighterFlow');s:AddInt(seat);s:AddInt(action);s:AddInt(menuEpoch);s:AddInt(flowRevision);s:SendSignal()
 if action==2 then leaveMatch('select')elseif action==3 then leaveMatch('home')end
end
local function retryFlow()
 if seat>0 and flowChoice[seat]==1 then local s=game.ServerSignal('FighterFlow');s:AddInt(seat);s:AddInt(1);s:AddInt(menuEpoch);s:AddInt(flowRevision);s:SendSignal()end
end
local function menuBind(name,callback)rootNode(name):AddCursorEventListener(Enum.CursorEventType.CursorClick,callback)end
local function beginRoundLoad(number,score)
 plannedRound=number;teamScores={score[1],score[2]};round=number;wins={score[1],score[2]}
 roleChoice={teamChoice[1][math.min(number,3)],teamChoice[2][math.min(number,3)]}
 menuReady={true,true};menuLoaded={false,false};onlineReady=false;joined=false;rb=nil;menuMode='roundload';menuDirty=true
 resourceGate.request('battle',roleChoice)
end
local function menuStart()
 script:RegisterServerSignalHandler('FighterTeamOut',function(_,p)
  local who,flag,map,epoch,revision,number,w1,w2=tonumber(p[1]),tonumber(p[5]),tonumber(p[6]),tonumber(p[7]),tonumber(p[8]),tonumber(p[9]),tonumber(p[10]),tonumber(p[11])
  if(who~=1 and who~=2)or who==seat or not flag or flag<0 or flag>3 or not map or map<1 or map>3 or not epoch or epoch<menuEpoch or not revision or revision<0 or not number or number<1 or number>3 or not w1 or not w2 or w1<0 or w2<0 or w1>2 or w2>2 then return end
  local team={tonumber(p[2]),tonumber(p[3]),tonumber(p[4])}
  for n=1,3 do if not team[n]or team[n]<0 or team[n]>__ROLE_COUNT__ or team[n]~=math.floor(team[n])then return end;for j=1,n-1 do if team[n]>0 and team[n]==team[j]then return end end end
  if(flag==1 or flag==2)and(team[1]==0 or team[2]==0 or team[3]==0)then return end
  local changed=epoch>menuEpoch
  if changed then
   local nextRound=who==1 and number>1 and(flag==1 or flag==2)and complete(seat)
   local rematching=number==1 and(flag==1 or flag==2)and flowChoice[seat]==1 and complete(seat)
   menuEpoch=epoch;menuSeen={-1,-1};menuRevision=menuRevision+1;onlineReady=false;joined=false;rb=nil;flowChoice={0,0};flowSeen={-1,-1}
   if nextRound then teamChoice[who]=team;stage=map;beginRoundLoad(number,{w1,w2})
   elseif rematching then plannedRound=1;teamScores={0,0};roleChoice={teamChoice[1][1],teamChoice[2][1]};menuMode='roundload';menuReady={true,true};menuLoaded={false,false};resourceGate.request('battle',roleChoice)
   else plannedRound=1;teamScores={0,0};teamChoice[seat]={0,0,0};previewChoice[seat]=0;menuMode=flag==3 and'home'or'select';menuReady={false,false};menuLoaded={false,false};resourceGate.request('menu',roleChoice)end
  end
  if revision<=menuSeen[who]then return end;menuSeen[who]=revision
  local oldPreview=previewChoice[who];teamChoice[who]=team;previewChoice[who]=team[3]>0 and team[3]or(team[2]>0 and team[2]or team[1])
  if who==1 then stage=map end
  roleChoice[who]=team[math.min(plannedRound,3)]>0 and team[math.min(plannedRound,3)]or roleChoice[who]
  menuReady[who]=(flag==1 or flag==2);menuLoaded[who]=flag==2;menuDirty=true
  if not changed and menuMode=='select'and oldPreview~=previewChoice[who]and resourceGate.mode=='menu'then resourceGate.request('menu',roleChoice)end
  if changed then sendSelection()end
 end)
 script:RegisterServerSignalHandler('FighterFlowOut',function(_,p)
  local who,action,epoch,revision=tonumber(p[1]),tonumber(p[2]),tonumber(p[3]),tonumber(p[4])
  if(who~=1 and who~=2)or who==seat or not epoch or(action==1 and epoch~=menuEpoch)or(action~=1 and(epoch<menuEpoch-1 or epoch>menuEpoch))or not revision or revision<=flowSeen[who]or(action~=1 and action~=2 and action~=3)then return end
  flowSeen[who]=revision;flowChoice[who]=action;menuDirty=true
  if action==2 or action==3 then leaveMatch(action==2 and'select'or'home',epoch+1)end
 end)
 menuBind('StartDuel',function()menuMode='select';if seat==1 then stage=math.random(1,3)end;menuRevision=menuRevision+1;menuDirty=true;sendSelection()end)
 for n=1,10 do local cell=n;menuBind('GridCard'..cell,function()local role=(rosterPage-1)*10+cell;if role<=__ROLE_COUNT__ then chooseRole(role)end end)end
 for i=1,2 do for n=1,3 do local who,at=i,n;menuBind('TeamSlot'..who..at,function()if who==seat and teamChoice[who][at]>0 then chooseRole(teamChoice[who][at])end end)end end
 local function page(delta)if resourceGate.busy then return end;rosterPage=(rosterPage-1+delta)%math.ceil(__ROLE_COUNT__/10)+1;menuDirty=true;resourceGate.request('menu',roleChoice)end
 menuBind('PagePrev',function()page(-1)end);menuBind('PageNext',function()page(1)end)
 menuBind('ReadyConfirm',setReady);menuBind('BackHome',function()sendFlow(3)end)
 menuBind('Rematch',function()sendFlow(1)end);menuBind('Reselect',function()sendFlow(2)end);menuBind('ResultHome',function()sendFlow(3)end)
 menuBind('DebugToggle',function()debugPanel=not debugPanel;menuDirty=true end)
 menuBind('CommandToggle',function()commandOpen=not commandOpen;menuDirty=true end);menuBind('CommandClose',function()commandOpen=false;menuDirty=true end)
 menuBind('ExitMatch',function()sendFlow(3)end)
 resourceGate.menuRoles=function()return previewChoice,rosterPage end
 resourceGate.completed=function(mode)
  spriteCache={};visualNodes={};visualValues={};visualCounts={};fxNodes={};fxPose={};portraitNodes={};portraitRole={};gridNodes={};gridRoles={};menuDirty=true
  if mode=='battle'then menuLoaded[seat]=true;menuRevision=menuRevision+1;sendSelection()end
 end
end
local function menuDraw()
 if resourceGate.busy then return end
 if onlineReady and phase=='roundLoad'then
  if seat==1 then menuEpoch=menuEpoch+1;menuRevision=menuRevision+1;menuSeen={-1,-1};beginRoundLoad(math.min(3,round+(roundWinner>0 and 1 or 0)),wins);sendSelection()
  else onlineReady=false;rb=nil;menuMode='waitingRound';menuDirty=true end
  return
 end
 if menuMode=='select'and menuReady[1]and menuReady[2]and not menuLoaded[seat]and resourceGate.mode~='battle'then
  plannedRound=1;teamScores={0,0};roleChoice={teamChoice[1][1],teamChoice[2][1]};menuMode='roundload';menuDirty=true;resourceGate.request('battle',roleChoice);return
 end
 if flowChoice[1]==1 and flowChoice[2]==1 then
  menuEpoch=menuEpoch+1;flowChoice={0,0};flowSeen={-1,-1};menuSeen={-1,-1};menuRevision=menuRevision+1;plannedRound=1;teamScores={0,0};roleChoice={teamChoice[1][1],teamChoice[2][1]}
  menuReady={true,true};menuLoaded={false,false};onlineReady=false;joined=false;rb=nil;menuMode='roundload';menuDirty=true;resourceGate.request('battle',roleChoice);sendSelection();return
 end
 local result=onlineReady and(wins[1]>=2 or wins[2]>=2)
 if not menuDirty then return end;menuDirty=false
 local selecting=menuMode=='select';local fighting=menuMode=='battle'
 local device=game.GetDevice();local touch=device==Enum.Device.Mobile or device==Enum.Device.MobileController
 rootNode('HomeScreen'):SetVisible(menuMode=='home');rootNode('SelectScreen'):SetVisible(selecting);rootNode('ResultScreen'):SetVisible(fighting and result)
 for _,name in ipairs({'Stats','Timer','Status','TopPanel','Meter1','Meter2','MeterBack1','MeterBack2','Energy1','Energy2','Name1','Name2','Hp1','Hp2','HpBack1','HpBack2','Combo1','Combo2','State1','State2'})do rootNode(name):SetVisible(fighting)end
 for _,name in ipairs({'Light','Heavy','Jump','Block','Skill','Ultimate','StickBase'})do rootNode(name):SetVisible(fighting and not result and touch and not commandOpen)end
 for d=1,9 do rootNode('Stick'..d):SetVisible(fighting and not result and touch and not commandOpen)end
 rootNode('Help'):SetVisible(false);rootNode('MotionHelp'):SetVisible(false);rootNode('Restart'):SetVisible(false)
 rootNode('Stats'):SetVisible(fighting and debugPanel);rootNode('BootDiagnostic'):SetVisible(debugPanel);rootNode('DebugToggle'):SetVisible(fighting)
 rootNode('CommandToggle'):SetVisible(fighting);rootNode('ExitMatch'):SetVisible(fighting);rootNode('CommandScreen'):SetVisible(commandOpen)
 local r=roleChoice[seat>0 and seat or 1];local s=moveNames[r]
 rootNode('CommandTitle').text=roleNames[r]..' · 指令表'
 rootNode('CommandBody').text='A / D  移动     S  蹲伏     空格  跳跃\nJ  轻攻击     K  重攻击     L  防御\nS + J  下段     前 + K  上段     S + K  升空\nE  '..s.special..'\nQ  '..s.super..' · 100 能量\nH  关闭指令表 · 联机战斗继续运行'
 for n=1,3 do rootNode('SelectStage'..n):SetVisible(false);rootNode('Stage'..n):SetVisible(fighting and stage==n)end
 rootNode('StageTitle'):SetVisible(fighting);rootNode('StageTitle').text=({'风起地 · 七天神像与大树','蒙德 · 城门与大桥','风龙废墟 · 中央高塔'})[stage]
 rootNode('RoleKeqing'):SetVisible(false);rootNode('RoleDiluc'):SetVisible(false)
 for i=1,2 do
  actors[i]:SetVisible(fighting);rootNode('Shadow'..i):SetVisible(fighting)
  local role=selecting and previewChoice[i]or roleChoice[i];local portrait=rootNode('Portrait'..i);portrait:SetVisible((selecting and role>0)or fighting)
  portrait:SetAnchoredPosition(selecting and(i==1 and -165 or 165)or(i==1 and -598 or 598),selecting and 160 or 285);drawPortrait(i,role)
  rootNode('SelectName'..i).text=role>0 and roleNames[role]or'选定角色后展示'
  rootNode('SelectReady'..i).text=menuReady[i]and'阵容已锁定'or'阵容尚未锁定'
  for n=1,3 do local chosen=teamChoice[i][n];rootNode('TeamName'..i..n).text=chosen>0 and roleNames[chosen]or'待选角色';plateColor('TeamSlot'..i..n..'Plate',chosen>0 and(i==1 and 0xff295a82 or 0xff8b3944)or 0xff2c3039)end
  for n=1,2 do rootNode('Win'..i..n):SetVisible(fighting and wins[i]>=n)end
 end
 for n=1,10 do local role=(rosterPage-1)*10+n;local valid=role<=__ROLE_COUNT__;rootNode('GridCard'..n):SetVisible(selecting and valid)
  if valid then
   local own=selected(1,role);local peer=selected(2,role)
   plateColor('GridPlate'..n,own and 0xff295a82 or(peer and 0xff8b3944 or 0xff40434b))
   rootNode('GridBlue'..n):SetVisible(own~=nil);rootNode('GridRed'..n):SetVisible(peer~=nil)
   gridNodes[n]=gridNodes[n]or{};paintFrame(rootNode('GridFace'..n),'IconPx',thumbData[role],2.3,gridNodes[n])
  end
 end
 rootNode('PageLabel').text=rosterPage..' / '..math.ceil(__ROLE_COUNT__/10)..'  ·  '..tostring(__ROLE_COUNT__)..' 位角色'
 local count=seat>0 and((teamChoice[seat][1]>0 and 1 or 0)+(teamChoice[seat][2]>0 and 1 or 0)+(teamChoice[seat][3]>0 and 1 or 0))or 0
 rootNode('SelectionHint').text=seat==0 and'等待席位…'or('你是玩家'..seat..' · 已选 '..count..'/3 · 点击已选角色可撤回')
 rootNode('ReadyConfirmText').text=seat>0 and menuReady[seat]and'取消锁定'or(count==3 and'锁定三人阵容'or'请选满三人')
 rootNode('ResultTitle').text=(wins[1]>=2 and'玩家1'or'玩家2')..'  获胜';rootNode('ResultScore').text=wins[1]..' : '..wins[2]..' · 三局两胜'..((flowChoice[1]==1 or flowChoice[2]==1)and' · 等待双方再战'or'')
end
