-- Original local fighting prototype. No third-party fighting engine code.
local root,actors,hpBars,status,timerText,stats
local tick,acc,phase,round,wins,remaining,freeze,intermission=0,0,'fight',1,{0,0},60,0,0
local input={left=false,right=false,down=false,block=false,light=0,heavy=0,special=0,jump=false}
local aiEnabled=false
local seat,onlineReady,joined,sendSeq,stateSeq,receivedState=0,false,false,0,0,0
local lastInputSeq={0,0}
local controls,controlPlayer={},1
local publishState
-- Absolute direction transitions, normalized against facing when an attack is pressed.
local directions,lastDirection,motionMove={},5,nil
local heldButtons={}
local commands={{sequence={6,2,3},button='heavy',move='rising'},{sequence={2,3,6},button='light',move='special'},{sequence={2,3,6},button='heavy',move='special'}}
local specs={
 {speed=235,light={startup=6,active=3,recovery=12,range=112,damage=8,stun=16,push=24},low={startup=7,active=4,recovery=16,range=120,damage=7,stun=17,push=18,height='low'},heavy={startup=17,active=4,recovery=25,range=150,damage=19,stun=27,push=45,height='high'},special={startup=11,active=8,recovery=26,range=138,damage=16,stun=25,push=36,dash=470}},
 {speed=180,light={startup=12,active=4,recovery=18,range=138,damage=12,stun=20,push=30},low={startup=13,active=4,recovery=21,range=145,damage=10,stun=20,push=22,height='low'},heavy={startup=25,active=5,recovery=31,range=180,damage=25,stun=33,push=52,height='high'},special={startup=27,active=7,recovery=35,range=240,damage=22,stun=31,push=48,}}
}
local f={{},{}}
local moveNames={{light='快剑',low='下段斩',heavy='重击',special='雷霆突进斩',rising='雷光升斩'},{light='挥剑',low='下段斩',heavy='重击',special='火焰重斩',rising='烈焰升斩'}}
local phaseNames={['KEQING WINS MATCH']='刻晴赢得比赛',['DILUC WINS MATCH']='迪卢克赢得比赛',['DRAW ROUND']='本回合平局',['KEQING WINS ROUND']='刻晴赢得本回合',['DILUC WINS ROUND']='迪卢克赢得本回合'}
specs[1].rising={startup=8,active=7,recovery=32,range=100,heightRange=190,damage=14,stun=27,push=25}
specs[2].rising={startup=12,active=8,recovery=38,range=125,heightRange=190,damage=18,stun=30,push=32}
local function recordDirection()
 local x=(input.right and 1 or 0)-(input.left and 1 or 0)
 local d=input.down and (x+2) or (x+5)
 if d~=lastDirection then directions[#directions+1]={d=d,t=tick};lastDirection=d end
 while #directions>32 do table.remove(directions,1)end
end
local function setDirection(key,value)input[key]=value;recordDirection()end
local function matchesMotion(sequence)
 local nextStep=#sequence;local newer=tick
 for n=#directions,1,-1 do
  local event=directions[n];local d=event.d
  if f[controlPlayer].face==-1 then if d==1 or d==3 then d=4-d elseif d==4 or d==6 then d=10-d end end
  if tick-event.t>24 or newer-event.t>12 then return false end
  if d~=5 then
   if d~=sequence[nextStep] then return false end
   if nextStep==#sequence and tick-event.t>8 then return false end
   nextStep=nextStep-1;newer=event.t
   if nextStep==0 then return true end
  end
 end
 return false
end
local function pressAttack(button)
 recordDirection()
 for _,command in ipairs(commands)do
  if command.button==button and matchesMotion(command.sequence)then
   input.light=0;input.heavy=0;input.special=12;motionMove=command.move;directions={};print('COMMAND '..command.move);return
  end
 end
 input[button]=12
end
local function clamp(x,a,b)return math.max(a,math.min(b,x))end
local function ready(i)local a=f[i];return a.hp>0 and a.stun<=0 and a.down<=0 and a.wake<=0 and not a.launched and not a.attack end
local function canCancel(i,kind)
 local a=f[i];local atk=a.attack
 if not atk or not atk.connected or a.stun>0 or a.down>0 or a.wake>0 or a.y>0 then return false end
 if atk.kind~='light' and atk.kind~='low' then return false end
 local s=specs[i][atk.kind];local t=atk.t-(atk.startup+s.active)
 if t<0 or t>8 then return false end
 return (kind=='light' and atk.kind=='light' and a.chainCount<2) or kind=='heavy' or kind=='special' or kind=='rising'
end
local function startAttack(i,kind)
 local a=f[i]
 local cancel=canCancel(i,kind)
 if not ready(i) and not cancel then return false end
 if (kind=='special' or kind=='rising' or kind=='low') and a.y>0 then return false end
 a.chainCount=cancel and a.chainCount+1 or 1
 local startup=specs[i][kind].startup
 if cancel and kind=='heavy' then startup=math.max(8,startup-6)end
 a.attack={kind=kind,t=0,hit=false,connected=false,startup=startup};a.crouch=kind=='low';a.block=false;return true
end
local function resetRound()
 for i=1,2 do f[i]={x=i==1 and -50 or 50,y=0,vy=0,hp=100,face=i==1 and 1 or -1,stun=0,down=0,wake=0,launched=false,airHits=0,attack=nil,block=false,crouch=false,chainCount=0,comboHits=0,comboDamage=0,comboOwner=0,comboDisplay=0,flash=0,walk=0}end
 remaining=60;phase='fight';freeze=0;intermission=0;acc=0;input={left=false,right=false,down=false,block=false,light=0,heavy=0,special=0,jump=false}
 directions={};lastDirection=5;motionMove=nil;heldButtons={}
 controls={}
 for i=1,2 do controls[i]={input={left=false,right=false,down=false,block=false,light=0,heavy=0,special=0,jump=false},directions={},lastDirection=5,heldButtons={}}end
 input=controls[1].input
end
local function withControl(i,callback)
 local savedInput,savedDirections,savedLast,savedMotion,savedHeld,savedPlayer=input,directions,lastDirection,motionMove,heldButtons,controlPlayer
 local c=controls[i];input=c.input;directions=c.directions;lastDirection=c.lastDirection;motionMove=c.motionMove;heldButtons=c.heldButtons;controlPlayer=i
 callback()
 c.directions=directions;c.lastDirection=lastDirection;c.motionMove=motionMove;c.heldButtons=heldButtons
 input=savedInput;directions=savedDirections;lastDirection=savedLast;motionMove=savedMotion;heldButtons=savedHeld;controlPlayer=savedPlayer
end
local function restart()round=1;wins={0,0};tick=0;resetRound()end
local function finish(winner)
 if winner>0 then wins[winner]=wins[winner]+1 end
 if wins[1]>=2 or wins[2]>=2 then phase=winner==1 and 'KEQING WINS MATCH' or 'DILUC WINS MATCH' else phase=winner==0 and 'DRAW ROUND' or (winner==1 and 'KEQING WINS ROUND' or 'DILUC WINS ROUND') end
 intermission=150;print('ROUND_END '..phase)
end
local function hit(i,j)
 local a,b=f[i],f[j];local atk=a.attack;local s=specs[i][atk.kind]
 if atk.hit or b.hp<=0 or b.down>0 or b.wake>0 or math.abs(b.y-a.y)>(s.heightRange or 75) then return end
 if b.launched and b.airHits>=5 then return end
 if s.height=='low' and b.y>20 then return end
 local distance=(b.x-a.x)*a.face
 if distance<0 or distance>s.range+20 then return end
 atk.hit=true
 local blocked=b.block and b.y==0 and b.face==-a.face and b.stun<=0 and not b.attack
 if s.height=='low' and not b.crouch then blocked=false end
 if s.height=='high' and b.crouch then blocked=false end
 local damage=blocked and math.max(1,math.floor(s.damage*.15)) or s.damage
 local airFollow=b.launched and not blocked
 if airFollow then damage=math.max(1,math.floor(damage*math.max(.4,1-.15*(b.airHits+1))))end
 if not blocked then
  atk.connected=true
  if b.stun>0 and b.comboOwner==i then a.comboHits=a.comboHits+1;a.comboDamage=a.comboDamage+damage else a.comboHits=1;a.comboDamage=damage end
  b.comboOwner=i;a.comboDisplay=90
 end
 b.hp=math.max(0,b.hp-damage);b.stun=blocked and 8 or s.stun;b.flash=blocked and 0 or 7;b.attack=nil;b.x=clamp(b.x+a.face*(blocked and 10 or (airFollow and s.push*.45 or s.push)),-535,535)
 if airFollow then
  b.airHits=b.airHits+1;b.stun=75;b.block=false;b.crouch=false
  if b.airHits>=5 or atk.kind=='heavy' or atk.kind=='special' then b.vy=math.min(b.vy,-300)
  elseif atk.kind=='rising' then b.vy=math.max(220,360-b.airHits*45)
  else b.vy=math.max(b.vy,240-b.airHits*25)end
  print('JUGGLE '..j..' count='..b.airHits)
 elseif not blocked and atk.kind=='rising' then
  b.launched=true;b.airHits=0;b.stun=75;b.block=false;b.crouch=false;b.y=math.max(b.y,8);b.vy=520;print('LAUNCH '..j)
 elseif not blocked and (atk.kind=='heavy' or atk.kind=='special') then
  b.down=45;b.stun=0;b.block=false;b.crouch=false;b.y=0;b.vy=0;print('KNOCKDOWN '..j)
 elseif not blocked and (atk.kind=='light' or atk.kind=='low') then b.stun=math.max(b.stun,24)end
 freeze=blocked and 2 or 4;print((blocked and 'BLOCK' or 'HIT')..' '..i..'>'..j..' damage='..damage..' move='..atk.kind)
end
local function advance(i)
 local a=f[i]
 if a.stun>0 then a.stun=a.stun-1 end
 if a.flash>0 then a.flash=a.flash-1 end
 if a.comboDisplay>0 then a.comboDisplay=a.comboDisplay-1 end
 if a.down>0 then a.down=a.down-1;if a.down==0 then a.wake=18;print('GETUP '..i)end;return end
 if a.wake>0 then a.wake=a.wake-1;return end
 if a.y>0 or a.vy>0 then
  a.y=a.y+a.vy/60;a.vy=a.vy-1100/60
  if a.launched and a.y>240 then a.y=240;a.vy=math.min(a.vy,0)end
  if a.y<=0 then
   a.y=0;a.vy=0
   if a.launched then a.launched=false;a.airHits=0;a.down=45;a.stun=0;a.attack=nil;print('AIR_LAND_KNOCKDOWN '..i)end
  end
 end
 if a.attack then
  local atk=a.attack;local s=specs[i][atk.kind];atk.t=atk.t+1
  if atk.t>=atk.startup and atk.t<atk.startup+s.active then hit(i,3-i)end
  if atk.t>=atk.startup+s.active+s.recovery then a.attack=nil;a.chainCount=0 end
 end
end
local function step()
 tick=tick+1
 if phase~='fight' then
  if wins[1]<2 and wins[2]<2 then intermission=intermission-1;if intermission<=0 then round=round+1;resetRound()end end;return
 end
 if freeze>0 then freeze=freeze-1;return end
 remaining=math.max(0,remaining-1/60)
 for i=1,2 do if ready(i) then f[i].face=f[3-i].x>=f[i].x and 1 or -1 end end
 local a,b=f[1],f[2]
 for i=1,2 do withControl(i,function()
  local p=f[i]
  input.light=math.max(0,input.light-1);input.heavy=math.max(0,input.heavy-1);input.special=math.max(0,input.special-1)
  if p.attack then
   if input.special>0 and startAttack(i,motionMove)then input.special=0 elseif input.heavy>0 and startAttack(i,'heavy')then input.heavy=0 elseif input.light>0 and startAttack(i,'light')then input.light=0 end
  end
  if ready(i) then
   p.crouch=input.down and p.y==0;p.block=input.block and p.y==0
   if input.special>0 and startAttack(i,motionMove)then input.special=0 elseif input.heavy>0 and startAttack(i,'heavy')then input.heavy=0 elseif input.light>0 and startAttack(i,p.crouch and 'low' or 'light')then input.light=0 end
   if not p.attack and not p.block and not p.crouch then local move=(input.right and 1 or 0)-(input.left and 1 or 0);p.x=clamp(p.x+move*specs[i].speed/60,-535,535);if move~=0 then p.walk=p.walk+.2 end end
   if input.jump and p.y==0 and not p.block and not p.attack then p.vy=465 end
  end
  input.jump=false
 end)end
 if aiEnabled and canCancel(2,'heavy') then startAttack(2,'heavy')end
 if aiEnabled and ready(2) then
  local dist=math.abs(a.x-b.x);b.block=false;b.crouch=false
  if a.attack and dist<170 and tick%90<50 and b.y==0 then b.block=true;b.crouch=specs[1][a.attack.kind].height=='low'
  elseif dist<250 and tick%100==0 then startAttack(2,a.y>30 and 'rising' or 'special')
  elseif dist>124 then b.x=clamp(b.x+b.face*specs[2].speed/60,-535,535);b.walk=b.walk+.16
  elseif tick%35==0 then startAttack(2,tick%105==0 and 'low' or (tick%70==0 and 'heavy' or 'light'))end
 end
 for i=1,2 do local c=f[i];if c.attack and c.attack.kind=='special' then local s=specs[i].special;if s.dash and c.attack.t>=s.startup-4 and c.attack.t<s.startup+s.active then c.x=clamp(c.x+c.face*s.dash/60,-535,535)end end end
 -- Ground pushboxes: neither fighter may overlap or swap sides while grounded.
 local gap=b.x-a.x
 if a.down<=0 and b.down<=0 and math.abs(gap)<50 and math.abs(a.y-b.y)<75 then local direction=gap>=0 and 1 or -1;local push=(50-math.abs(gap))/2;a.x=clamp(a.x-direction*push,-535,535);b.x=clamp(b.x+direction*push,-535,535)end
 advance(1);advance(2)
 if a.hp<=0 or b.hp<=0 or remaining<=0 then finish(a.hp==b.hp and 0 or (a.hp>b.hp and 1 or 2))end
end
local function draw()
 for i=1,2 do
  local a,art=f[i],actors[i]:FindChild('Art')
  actors[i]:SetAnchoredPosition(a.x,-155+a.y);art:SetLocalScale(a.face,a.crouch and .60 or 1,1)
  art:SetLocalRotation(0,0,a.down>0 and -90*a.face or (a.launched and -35*a.face or 0))
  art:SetAnchoredPosition(0,a.down>0 and 18 or 0)
  local swing=0
  if a.attack then local s=specs[i][a.attack.kind];swing=a.attack.t<a.attack.startup and -35 or (a.attack.t<a.attack.startup+s.active and 0 or 20);if a.attack.kind=='low' then swing=-12 end end
  art:FindChild('Sword'):SetLocalRotation(0,0,swing);art:FindChild('Arm'):SetLocalRotation(0,0,swing*.4)
  art:FindChild('Sword'):SetVisible(a.down<=0);art:FindChild('Arm'):SetVisible(a.down<=0)
  local gait=math.sin(a.walk)*13;art:FindChild('BackLeg'):SetLocalRotation(0,0,gait);art:FindChild('FrontLeg'):SetLocalRotation(0,0,-gait)
  actors[i]:FindChild('Flash'):SetVisible(a.flash>0 and a.down<=0);actors[i]:FindChild('GuardVisual'):SetVisible(a.block);actors[i]:FindChild('GuardVisual'):SetAnchoredPosition(a.face*46,a.crouch and 62 or 115)
  actors[i]:FindChild('Hitbox'):SetVisible(a.attack~=nil and a.attack.hit);actors[i]:FindChild('Hitbox'):SetAnchoredPosition(a.face*110,a.crouch and 45 or 120)
  local fx=actors[i]:FindChild('SpecialFx');fx:SetLocalScale(a.face,1,1);fx:SetVisible(a.attack~=nil and (a.attack.kind=='special' or a.attack.kind=='rising'));fx:SetLocalRotation(0,0,a.attack and a.attack.kind=='rising' and 65*a.face or 0);if a.attack then fx:SetAnchoredPosition(a.face*100,95)end
  hpBars[i]:SetSizeDelta(math.max(1,480*a.hp/100),19);hpBars[i]:SetAnchoredPosition((i==1 and -565 or 565)+(i==1 and 1 or -1)*240*a.hp/100,264)
  root:FindChild(i==1 and 'Combo1' or 'Combo2').text=a.comboDisplay>0 and (a.comboHits..' 连击 / '..a.comboDamage..' 伤害') or ''
  root:FindChild(i==1 and 'State1' or 'State2').text=a.launched and ('浮空 / 追击 '..a.airHits..'/5') or (a.down>0 and '倒地' or (a.wake>0 and '起身保护' or ''))
 end
 timerText.text=tostring(math.ceil(remaining));status.text=not onlineReady and '等待双人模式：玩家1刻晴 / 玩家2迪卢克' or (phase=='fight' and ('第 '..round..' 回合 | '..wins[1]..' - '..wins[2]) or phaseNames[phase])
 stats.text='生命 '..f[1].hp..' / '..f[2].hp..' | '..(f[1].attack and moveNames[1][f[1].attack.kind] or (f[1].block and (f[1].crouch and '蹲防' or '站防') or '就绪'))..' | '..(f[2].attack and moveNames[2][f[2].attack.kind] or (f[2].block and '防御' or '电脑对手'))..' | 必杀 236+J/K / 挑飞 623+K'
 stats.text='同步帧 '..tick..' | '..string.gsub(stats.text,'电脑对手','就绪')
end
function OnInit()
 root=script.object;actors={root:FindChild('Keqing'),root:FindChild('Diluc')};hpBars={root:FindChild('Hp1'),root:FindChild('Hp2')};status=root:FindChild('Status');timerText=root:FindChild('Timer');stats=root:FindChild('Stats');restart();draw()
end
local function bind(name,callback)root:AddKeyEventListener(Enum.KeyEventType[name],function()callback();return true end)end
local fields={'x','y','vy','hp','face','stun','down','wake','launched','airHits','block','crouch','chainCount','comboHits','comboDamage','comboOwner','comboDisplay','flash','walk'}
local boolFields={launched=true,block=true,crouch=true}
local function packState()
 local values={}
 local function add(v)values[#values+1]=type(v)=='number' and string.format('%.17g',v) or tostring(v)end
 add(tick);add(acc);add(phase);add(round);add(wins[1]);add(wins[2]);add(remaining);add(freeze);add(intermission)
 for i=1,2 do local p=f[i]
  for _,key in ipairs(fields)do add(boolFields[key] and (p[key] and 1 or 0) or p[key])end
  local atk=p.attack;add(atk and atk.kind or 'none');add(atk and atk.t or 0);add(atk and atk.hit and 1 or 0);add(atk and atk.connected and 1 or 0);add(atk and atk.startup or 0)
 end
 return table.concat(values,'|')
end
local function unpackState(data)
 local values={};for v in string.gmatch(data,'[^|]+')do values[#values+1]=v end
 if #values~=57 then print('NET_BAD_STATE '..#values);return false end
 local index=0;local function get()index=index+1;return values[index]end;local function num()return tonumber(get())or 0 end
 tick=num();acc=num();phase=get();round=num();wins={num(),num()};remaining=num();freeze=num();intermission=num()
 for i=1,2 do local p=f[i]
  for _,key in ipairs(fields)do local value=num();if boolFields[key]then p[key]=value==1 else p[key]=value end end
  local kind=get();local t,hit,connected,startup=num(),num(),num(),num();p.attack=kind~='none' and {kind=kind,t=t,hit=hit==1,connected=connected==1,startup=startup}or nil
 end
 draw();return true
end
publishState=function()
 if seat~=1 or not onlineReady then return end
 stateSeq=stateSeq+1;local sig=game.ServerSignal('FighterState');sig:AddInt(stateSeq);sig:AddString(packState());sig:SendSignal()
end
local function applyInput(player,event,value)
 if event=='restart' then restart();return end
 withControl(player,function()
  if event=='left' or event=='right' or event=='down' or event=='block' then setDirection(event,value==1)
  elseif event=='jump' then input.jump=true
  elseif event=='light' or event=='heavy' then
   if value==0 then heldButtons[event]=false elseif not heldButtons[event]then heldButtons[event]=true;pressAttack(event)end
  elseif event=='clickLight' then pressAttack('light')elseif event=='clickHeavy' then pressAttack('heavy')end
 end)
end
local function sendInput(event,value)
 if seat<1 or not onlineReady then return end
 sendSeq=sendSeq+1;local sig=game.ServerSignal('FighterInput');sig:AddInt(seat);sig:AddInt(sendSeq);sig:AddString(event);sig:AddInt(value or 1);sig:SendSignal()
end
function OnStart()
 script:RegisterServerSignalHandler('FighterStateOut',function(_,params)
  if seat~=2 then return end
  local seq=tonumber(params[1])or 0;if seq<=receivedState then return end
  if unpackState(params[2])then receivedState=seq end
 end)
 script:RegisterServerSignalHandler('FighterInputOut',function(_,params)
  if seat~=1 or not onlineReady then return end
  local player,seq=tonumber(params[1]),tonumber(params[2]);if (player~=1 and player~=2)or not seq or seq<=lastInputSeq[player]then return end
  lastInputSeq[player]=seq;applyInput(player,params[3],tonumber(params[4])or 0);draw();publishState()
 end)
 script:RegisterServerSignalHandler('FighterJoined',function()
  if not onlineReady then onlineReady=true;restart()end
  draw();publishState()
 end)
 script:RegisterServerSignalHandler('FighterSeat',function(_,params)
  seat=tonumber(params[1])or 0
  if seat==2 and not joined then joined=true;game.ServerSignal('FighterJoin'):SendSignal()end
 end)
 bind('KeyboardMoveLeftKeyDown',function()sendInput('left',1)end);bind('KeyboardMoveLeftKeyUp',function()sendInput('left',0)end)
 bind('KeyboardMoveRightKeyDown',function()sendInput('right',1)end);bind('KeyboardMoveRightKeyUp',function()sendInput('right',0)end)
 bind('KeyboardJumpKeyDown',function()sendInput('jump')end)
 bind('KeyboardMoveBackwardKeyDown',function()sendInput('down',1)end);bind('KeyboardMoveBackwardKeyUp',function()sendInput('down',0)end)
 bind('KeyboardCraftspersonKey19Down',function()sendInput('light',1)end);bind('KeyboardCraftspersonKey19Up',function()sendInput('light',0)end)
 bind('KeyboardCraftspersonKey20Down',function()sendInput('heavy',1)end);bind('KeyboardCraftspersonKey20Up',function()sendInput('heavy',0)end)
 bind('KeyboardCraftspersonKey21Down',function()sendInput('block',1)end);bind('KeyboardCraftspersonKey21Up',function()sendInput('block',0)end)
 bind('KeyboardCharacterSkill3KeyDown',function()sendInput('restart')end)
 for _,entry in ipairs({{'Left','left'},{'Right','right'},{'Down','down'},{'Block','block'}})do
  local c,k=root:FindChild(entry[1]),entry[2]
  c:AddCursorEventListener(Enum.CursorEventType.CursorDown,function()sendInput(k,1)end)
  c:AddCursorEventListener(Enum.CursorEventType.CursorUp,function()sendInput(k,0)end)
  c:AddCursorEventListener(Enum.CursorEventType.CursorExit,function()sendInput(k,0)end)
 end
 for _,entry in ipairs({{'Light',function()sendInput('clickLight')end},{'Heavy',function()sendInput('clickHeavy')end},{'Jump',function()sendInput('jump')end},{'Restart',function()sendInput('restart')end}})do root:FindChild(entry[1]):AddCursorEventListener(Enum.CursorEventType.CursorClick,entry[2])end
 script:EnableUpdate(true)
 game.ServerSignal('FighterHello'):SendSignal()
end
function OnDisable()input.left=false;input.right=false;input.down=false;input.block=false;input.light=0;input.heavy=0;input.special=0;directions={};lastDirection=5;motionMove=nil;heldButtons={} end
function OnUpdate(dt)
 if seat~=1 or not onlineReady then return end
 acc=acc+math.min(dt,.1);local n=0;while acc>=1/60 and n<6 do acc=acc-1/60;n=n+1;step()end;draw()
 publishState()
end
