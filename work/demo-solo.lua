-- Original local fighting prototype. No third-party fighting engine code.
local root,actors,hpBars,status,timerText,stats
local tick,acc,phase,round,wins,remaining,freeze,intermission=0,0,'fight',1,{0,0},60,0,0
local stage,roleChoice=1,{1,2}
local input={left=false,right=false,down=false,block=false,light=0,heavy=0,special=0,jump=false}
local aiEnabled=true
-- Absolute direction transitions, normalized against facing when an attack is pressed.
local directions,lastDirection,motionMove={},5,nil
local heldButtons={}
local commands={{sequence={2,3,6,2,3,6},button='heavy',move='super'},{sequence={6,2,3},button='heavy',move='rising'},{sequence={2,3,6},button='light',move='special'},{sequence={2,3,6},button='heavy',move='special'}}
local specs={
 {speed=235,light={startup=6,active=3,recovery=12,range=112,damage=8,stun=16,push=24},low={startup=7,active=4,recovery=16,range=120,damage=7,stun=17,push=18,height='low'},heavy={startup=17,active=4,recovery=25,range=150,damage=19,stun=27,push=45,height='high'},special={startup=11,active=8,recovery=26,range=138,damage=16,stun=25,push=36,dash=470}},
 {speed=180,light={startup=12,active=4,recovery=18,range=138,damage=12,stun=20,push=30},low={startup=13,active=4,recovery=21,range=145,damage=10,stun=20,push=22,height='low'},heavy={startup=25,active=5,recovery=31,range=180,damage=25,stun=33,push=52,height='high'},special={startup=27,active=7,recovery=35,range=240,damage=22,stun=31,push=48,}}
}
local f={{},{}}
local moveNames={{light='快剑',low='下段斩',heavy='重击',special='雷霆突进斩',rising='雷光升斩'},{light='挥剑',low='下段斩',heavy='重击',special='火焰重斩',rising='烈焰升斩'}}
local phaseNames={['KEQING WINS MATCH']='刻晴赢得比赛',['DILUC WINS MATCH']='迪卢克赢得比赛',['DRAW ROUND']='本回合平局',['KEQING WINS ROUND']='刻晴赢得本回合',['DILUC WINS ROUND']='迪卢克赢得本回合'}
specs[1].rising={startup=8,active=7,recovery=32,range=100,heightRange=190,damage=14,stun=27,push=25}
specs[2].rising={startup=12,active=8,recovery=38,range=125,heightRange=190,damage=18,stun=30,push=32}
specs[1].super={startup=16,active=10,recovery=38,range=310,heightRange=220,damage=38,stun=40,push=65}
specs[2].super={startup=24,active=12,recovery=45,range=370,heightRange=220,damage=44,stun=44,push=75}
moveNames[1].super='天街巡游';moveNames[2].super='黎明'
specs[1].overhead={startup=21,active=4,recovery=26,range=140,damage=18,stun=26,push=42,height='high'}
specs[2].overhead={startup=29,active=5,recovery=32,range=175,damage=24,stun=32,push=50,height='high'}
moveNames[1].overhead='上段斩';moveNames[2].overhead='上段斩'
-- Neutral heavy is mid. Forward + heavy is overhead; down + light is low.
specs[1].heavy.height=nil;specs[2].heavy.height=nil
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
  if f[1].face==-1 then if d==1 or d==3 then d=4-d elseif d==4 or d==6 then d=10-d end end
  if tick-event.t>(#sequence>3 and 42 or 24) or newer-event.t>12 then return false end
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
 local s=specs[f[i].role][atk.kind];local t=atk.t-(atk.startup+s.active)
 if t<0 or t>8 then return false end
 return (kind=='light' and atk.kind=='light' and a.chainCount<2) or kind=='heavy' or kind=='special' or kind=='rising' or kind=='super' or kind=='overhead'
end
local function startAttack(i,kind)
 local a=f[i]
 if kind=='heavy' then
 local c=i==1 and input or {}
 if (a.face==1 and c.right) or (a.face==-1 and c.left) then kind='overhead' end
end
local cancel=canCancel(i,kind)
 if not ready(i) and not cancel then return false end
 if (kind=='special' or kind=='rising' or kind=='low') and a.y>0 then return false end
 if kind=='super' and (a.meter<100 or a.y>0) then return false end
 if kind=='super' then a.meter=a.meter-100;print('SUPER '..i)end
 a.chainCount=cancel and a.chainCount+1 or 1
 local startup=specs[f[i].role][kind].startup
 if cancel and kind=='heavy' then startup=math.max(8,startup-6)end
 a.attack={kind=kind,t=0,hit=false,connected=false,startup=startup};a.crouch=kind=='low';a.block=false;return true
end
local function resetRound()
 for i=1,2 do f[i]={x=i==1 and -230 or 230,y=0,vy=0,hp=100,role=roleChoice[i],meter=0,face=i==1 and 1 or -1,stun=0,down=0,wake=0,launched=false,airHits=0,attack=nil,block=false,crouch=false,chainCount=0,comboHits=0,comboDamage=0,comboOwner=0,comboDisplay=0,flash=0,walk=0}end
 remaining=60;phase='fight';freeze=0;intermission=0;acc=0;input={left=false,right=false,down=false,block=false,light=0,heavy=0,special=0,jump=false}
 directions={};lastDirection=5;motionMove=nil;heldButtons={}
end
local function restart()round=1;wins={0,0};tick=0;resetRound()end
local function finish(winner)
 if winner>0 then wins[winner]=wins[winner]+1 end
 if wins[1]>=2 or wins[2]>=2 then phase=winner==1 and 'KEQING WINS MATCH' or 'DILUC WINS MATCH' else phase=winner==0 and 'DRAW ROUND' or (winner==1 and 'KEQING WINS ROUND' or 'DILUC WINS ROUND') end
 intermission=150;print('ROUND_END '..phase)
end
local function hit(i,j)
 local a,b=f[i],f[j];local atk=a.attack;local s=specs[f[i].role][atk.kind]
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
 a.meter=math.min(100,a.meter+(blocked and 4 or damage*.9));b.meter=math.min(100,b.meter+damage*1.2);
 b.hp=math.max(0,b.hp-damage);b.stun=blocked and 8 or s.stun;b.flash=blocked and 0 or 7;b.attack=nil;b.x=clamp(b.x+a.face*(blocked and 10 or (airFollow and s.push*.45 or s.push)),-535,535)
 if airFollow then
  b.airHits=b.airHits+1;b.stun=75;b.block=false;b.crouch=false
  if b.airHits>=5 or atk.kind=='heavy' or atk.kind=='overhead' or atk.kind=='super' or atk.kind=='special' then b.vy=math.min(b.vy,-300)
  elseif atk.kind=='rising' then b.vy=math.max(220,360-b.airHits*45)
  else b.vy=math.max(b.vy,240-b.airHits*25)end
  print('JUGGLE '..j..' count='..b.airHits)
 elseif not blocked and atk.kind=='rising' then
  b.launched=true;b.airHits=0;b.stun=75;b.block=false;b.crouch=false;b.y=math.max(b.y,8);b.vy=520;print('LAUNCH '..j)
 elseif not blocked and (atk.kind=='heavy' or atk.kind=='overhead' or atk.kind=='super' or atk.kind=='special') then
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
  local atk=a.attack;local s=specs[f[i].role][atk.kind];atk.t=atk.t+1
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
 for i=1,2 do f[i].meter=math.min(100,f[i].meter+.045)end
 remaining=math.max(0,remaining-1/60)
 for i=1,2 do if ready(i) then f[i].face=f[3-i].x>=f[i].x and 1 or -1 end end
 local a,b=f[1],f[2]
 input.light=math.max(0,input.light-1);input.heavy=math.max(0,input.heavy-1);input.special=math.max(0,input.special-1)
 if a.attack then
  if input.special>0 and startAttack(1,motionMove)then input.special=0 elseif input.heavy>0 and startAttack(1,'heavy')then input.heavy=0 elseif input.light>0 and startAttack(1,'light')then input.light=0 end
 end
 if ready(1) then
  a.crouch=input.down and a.y==0
  a.block=input.block and a.y==0
  if input.special>0 and startAttack(1,motionMove)then input.special=0 elseif input.heavy>0 and startAttack(1,'heavy')then input.heavy=0 elseif input.light>0 and startAttack(1,a.crouch and 'low' or 'light')then input.light=0 end
  if not a.attack and not a.block and not a.crouch then local move=(input.right and 1 or 0)-(input.left and 1 or 0);a.x=clamp(a.x+move*specs[a.role].speed/60,-535,535);if move~=0 then a.walk=a.walk+.2 end end
  if input.jump and a.y==0 and not a.block and not a.attack then a.vy=465 end
 end
 input.jump=false
 if aiEnabled and canCancel(2,'heavy') then startAttack(2,'heavy')end
 if aiEnabled and ready(2) then
  local dist=math.abs(a.x-b.x);b.block=false;b.crouch=false
  if a.attack and dist<170 and tick%90<50 and b.y==0 then b.block=true;b.crouch=specs[a.role][a.attack.kind].height=='low'
  elseif b.meter>=100 and dist<330 and tick%90==0 then startAttack(2,'super')
  elseif dist<250 and tick%(b.role==1 and 80 or 100)==0 then startAttack(2,a.y>30 and 'rising' or 'special')
  elseif dist>(b.role==1 and 98 or 124) then b.x=clamp(b.x+b.face*specs[b.role].speed/60,-535,535);b.walk=b.walk+.16
  elseif tick%35==0 then startAttack(2,tick%105==0 and 'low' or (tick%70==0 and 'heavy' or 'light'))end
 end
 for i=1,2 do local c=f[i];if c.attack and c.attack.kind=='special' then local s=specs[f[i].role].special;if s.dash and c.attack.t>=s.startup-4 and c.attack.t<s.startup+s.active then c.x=clamp(c.x+c.face*s.dash/60,-535,535)end end end
 -- Ground pushboxes: neither fighter may overlap or swap sides while grounded.
 local gap=b.x-a.x
 if a.down<=0 and b.down<=0 and math.abs(gap)<50 and math.abs(a.y-b.y)<75 then local direction=gap>=0 and 1 or -1;local push=(50-math.abs(gap))/2;a.x=clamp(a.x-direction*push,-535,535);b.x=clamp(b.x+direction*push,-535,535)end
 advance(1);advance(2)
 if a.hp<=0 or b.hp<=0 or remaining<=0 then finish(a.hp==b.hp and 0 or (a.hp>b.hp and 1 or 2))end
end

local spriteData=SPRITE_DATA
local spriteCache={}
local function updateSprite(i)
 local a=f[i];local art=actors[i]:FindChild('Art');local pose=1
 if a.attack then local s=specs[a.role][a.attack.kind];pose=a.attack.t<a.attack.startup and 2 or (a.attack.kind=='rising' and 4 or 3);if a.attack.t>a.attack.startup+s.active+s.recovery*.6 then pose=1 end end
 local key=a.role*10+pose
 if spriteCache[i]~=key then
  local data=spriteData[a.role][pose];local pool=art:FindChild('Sprite')
  for n=1,SPRITE_POOL do
   local node=pool:FindChild('P'..n);local r=data.rows[n]
   node:SetVisible(r~=nil)
   if r then node:SetAnchoredPosition((r[1]+r[3]/2-data.anchor[1])*data.scale,(data.anchor[2]-r[2]-r[4]/2)*data.scale);node:SetSizeDelta(r[3]*data.scale,r[4]*data.scale);node.imageColor=r[5] end
  end
  spriteCache[i]=key
 end
 -- Demo uses complete source key poses; pool attributes update only when the pose or role changes.
 local lean=a.attack and (a.attack.t<a.attack.startup and 7 or -8) or (a.stun>0 and 12 or math.sin(a.walk)*1.3)
 art:SetLocalRotation(0,0,a.down>0 and -90*a.face or (a.launched and -35*a.face or lean*a.face))
 local roles={'刻晴','迪卢克'};root:FindChild(i==1 and 'Name1' or 'Name2').text=roles[a.role]..(i==1 and ' / 玩家1' or (aiEnabled and ' / 电脑' or ' / 玩家2'))
 local meter=root:FindChild(i==1 and 'Meter1' or 'Meter2');meter:SetSizeDelta(math.max(1,a.meter*4.8),8)
 meter:SetAnchoredPosition((i==1 and -565 or 565)+(i==1 and 1 or -1)*a.meter*2.4,245)
 root:FindChild(i==1 and 'Energy1' or 'Energy2').text='能量 '..math.floor(a.meter)..'/100'..(a.meter>=100 and ' · 超必杀就绪' or '')
end
local function drawStage()
 for n=1,3 do root:FindChild('Stage'..n):SetVisible(stage==n)end
 root:FindChild('StageTitle').text=({'风起地 · 大树前','蒙德 · 城门大桥','风龙废墟 · 外围'})[stage]
end

local function draw()
 for i=1,2 do
  local a,art=f[i],actors[i]:FindChild('Art')
  actors[i]:SetAnchoredPosition(a.x,-155+a.y);art:SetLocalScale(a.face,a.crouch and .60 or 1,1)
  art:SetLocalRotation(0,0,a.down>0 and -90*a.face or (a.launched and -35*a.face or 0))
  art:SetAnchoredPosition(0,a.down>0 and 18 or 0)
  local swing=0
  if a.attack then local s=specs[f[i].role][a.attack.kind];swing=a.attack.t<a.attack.startup and -35 or (a.attack.t<a.attack.startup+s.active and 0 or 20);if a.attack.kind=='low' then swing=-12 end end
  updateSprite(i)
  actors[i]:FindChild('Flash'):SetVisible(a.flash>0 and a.down<=0);actors[i]:FindChild('GuardVisual'):SetVisible(a.block);actors[i]:FindChild('GuardVisual'):SetAnchoredPosition(a.face*46,a.crouch and 62 or 115)
  actors[i]:FindChild('Hitbox'):SetVisible(false);actors[i]:FindChild('Hitbox'):SetAnchoredPosition(a.face*110,a.crouch and 45 or 120)
  local fx=actors[i]:FindChild('SpecialFx');fx:SetLocalScale(a.face,1,1);fx:SetVisible(a.attack~=nil and (a.attack.kind=='special' or a.attack.kind=='rising' or a.attack.kind=='super'));fx:SetLocalRotation(0,0,a.attack and a.attack.kind=='rising' and 65*a.face or 0);if a.attack then fx:SetAnchoredPosition(a.face*100,95)end
  hpBars[i]:SetSizeDelta(math.max(1,480*a.hp/100),19);hpBars[i]:SetAnchoredPosition((i==1 and -565 or 565)+(i==1 and 1 or -1)*240*a.hp/100,264)
  root:FindChild(i==1 and 'Combo1' or 'Combo2').text=a.comboDisplay>0 and (a.comboHits..' 连击 / '..a.comboDamage..' 伤害') or ''
  root:FindChild(i==1 and 'State1' or 'State2').text=a.launched and ('浮空 / 追击 '..a.airHits..'/5') or (a.down>0 and '倒地' or (a.wake>0 and '起身保护' or ''))
 end
 drawStage()
 timerText.text=tostring(math.ceil(remaining));status.text=phase=='fight' and ('第 '..round..' 回合 | '..wins[1]..' - '..wins[2]) or (phase=='DRAW ROUND' and '本回合平局' or (({'刻晴','迪卢克'})[f[(wins[1]>=2 or phase=='KEQING WINS ROUND') and 1 or 2].role]..((wins[1]>=2 or wins[2]>=2) and '赢得比赛' or '赢得本回合')))
 stats.text='生命 '..f[1].hp..' / '..f[2].hp..' | '..(f[1].attack and moveNames[f[1].role][f[1].attack.kind] or (f[1].block and (f[1].crouch and '蹲防' or '站防') or '就绪'))..' | '..(f[2].attack and moveNames[f[2].role][f[2].attack.kind] or (f[2].block and '防御' or '电脑对手'))..' | 必杀 236+J/K / 挑飞 623+K / 超必杀 236236+K'
end
function OnInit()
 root=script.object;actors={root:FindChild('Keqing'),root:FindChild('Diluc')};hpBars={root:FindChild('Hp1'),root:FindChild('Hp2')};status=root:FindChild('Status');timerText=root:FindChild('Timer');stats=root:FindChild('Stats');restart();draw()
end
local function bind(name,callback)root:AddKeyEventListener(Enum.KeyEventType[name],function()callback();return true end)end
function OnStart()
 bind('KeyboardMoveLeftKeyDown',function()setDirection('left',true)end);bind('KeyboardMoveLeftKeyUp',function()setDirection('left',false)end)
 bind('KeyboardMoveRightKeyDown',function()setDirection('right',true)end);bind('KeyboardMoveRightKeyUp',function()setDirection('right',false)end)
 bind('KeyboardJumpKeyDown',function()input.jump=true end)
 bind('KeyboardMoveBackwardKeyDown',function()setDirection('down',true)end);bind('KeyboardMoveBackwardKeyUp',function()setDirection('down',false)end)
 bind('KeyboardCraftspersonKey19Down',function()if not heldButtons.light then heldButtons.light=true;pressAttack('light')end end)
 bind('KeyboardCraftspersonKey19Up',function()heldButtons.light=false end)
 bind('KeyboardCraftspersonKey20Down',function()if not heldButtons.heavy then heldButtons.heavy=true;pressAttack('heavy')end end)
 bind('KeyboardCraftspersonKey20Up',function()heldButtons.heavy=false end)
 bind('KeyboardCraftspersonKey21Down',function()input.block=true end);bind('KeyboardCraftspersonKey21Up',function()input.block=false end)
 bind('KeyboardCharacterSkill3KeyDown',restart)
 for _,entry in ipairs({{'Left','left'},{'Right','right'},{'Down','down'},{'Block','block'}})do
  local c,k=root:FindChild(entry[1]),entry[2]
  c:AddCursorEventListener(Enum.CursorEventType.CursorDown,function()setDirection(k,true)end)
  c:AddCursorEventListener(Enum.CursorEventType.CursorUp,function()setDirection(k,false)end)
  c:AddCursorEventListener(Enum.CursorEventType.CursorExit,function()setDirection(k,false)end)
 end
 for _,entry in ipairs({{'Light',function()pressAttack('light')end},{'Heavy',function()pressAttack('heavy')end},{'Jump',function()input.jump=true end},{'Restart',restart}})do root:FindChild(entry[1]):AddCursorEventListener(Enum.CursorEventType.CursorClick,entry[2])end

 for _,e in ipairs({{'RoleKeqing',1},{'RoleDiluc',2}})do root:FindChild(e[1]):AddCursorEventListener(Enum.CursorEventType.CursorClick,function()roleChoice={e[2],3-e[2]};spriteCache={};restart();draw()end)end
 for n=1,3 do root:FindChild('SelectStage'..n):AddCursorEventListener(Enum.CursorEventType.CursorClick,function()stage=n;draw()end)end

 local stickHeld=false
 local function stick(d)
  local x=(d==1 or d==4 or d==7) and -1 or ((d==3 or d==6 or d==9) and 1 or 0)
  local down=d<=3
  input.left=x<0;input.right=x>0;input.down=down;recordDirection();if d>=7 then input.jump=true end
 end
 for d=1,9 do local c=root:FindChild('Stick'..d)
  c:AddCursorEventListener(Enum.CursorEventType.CursorDown,function()stickHeld=true;stick(d)end)
  c:AddCursorEventListener(Enum.CursorEventType.CursorEnter,function()if stickHeld then stick(d)end end)
  c:AddCursorEventListener(Enum.CursorEventType.CursorUp,function()stickHeld=false;stick(5)end)
  c:AddCursorEventListener(Enum.CursorEventType.CursorDrag,function(event)
   local x,y=event:GetUIPos();local px,py=event:GetPressUIPos()
   local dx=x-px+((d-1)%3-1)*48;local dy=y-py+(math.floor((d-1)/3)-1)*48
   local sx=dx>20 and 1 or (dx< -20 and -1 or 0);local sy=dy>20 and 1 or (dy< -20 and -1 or 0)
   stick(5+sx+sy*3)
  end)
  c:AddCursorEventListener(Enum.CursorEventType.CursorEndDrag,function()stickHeld=false;stick(5)end)
 end

 script:EnableUpdate(true)
end
function OnDisable()input.left=false;input.right=false;input.down=false;input.block=false;input.light=0;input.heavy=0;input.special=0;directions={};lastDirection=5;motionMove=nil;heldButtons={} end
function OnUpdate(dt)
 acc=acc+math.min(dt,.1);local n=0;while acc>=1/60 and n<6 do acc=acc-1/60;n=n+1;step()end;draw()
end
