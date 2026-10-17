-- Original local fighting prototype. No third-party fighting engine code.
local root,actors,hpBars,status,timerText,stats
local tick,acc,phase,round,wins,remaining,freeze,intermission=0,0,'fight',1,{0,0},60,0,0
local input={left=false,right=false,down=false,block=false,light=0,heavy=0,special=0,jump=false}
local aiEnabled=true
local specs={
 {speed=235,light={startup=6,active=3,recovery=12,range=112,damage=8,stun=16,push=24},low={startup=7,active=4,recovery=16,range=120,damage=7,stun=17,push=18,height='low'},heavy={startup=17,active=4,recovery=25,range=150,damage=19,stun=27,push=45,height='high'},special={startup=11,active=8,recovery=26,range=138,damage=16,stun=25,push=36,cooldown=180,dash=470}},
 {speed=180,light={startup=12,active=4,recovery=18,range=138,damage=12,stun=20,push=30},low={startup=13,active=4,recovery=21,range=145,damage=10,stun=20,push=22,height='low'},heavy={startup=25,active=5,recovery=31,range=180,damage=25,stun=33,push=52,height='high'},special={startup=27,active=7,recovery=35,range=240,damage=22,stun=31,push=48,cooldown=300}}
}
local f={{},{}}
local function clamp(x,a,b)return math.max(a,math.min(b,x))end
local function ready(i)local a=f[i];return a.hp>0 and a.stun<=0 and not a.attack end
local function startAttack(i,kind)
 if not ready(i) then return false end
 local a=f[i]
 if (kind=='special' and (a.cooldown>0 or a.y>0)) or (kind=='low' and a.y>0) then return false end
 if kind=='special' then a.cooldown=specs[i].special.cooldown end
 a.attack={kind=kind,t=0,hit=false};a.crouch=kind=='low';a.block=false;a.combo=kind=='light' and a.combo+1 or 0;return true
end
local function resetRound()
 for i=1,2 do f[i]={x=i==1 and -230 or 230,y=0,vy=0,hp=100,face=i==1 and 1 or -1,stun=0,attack=nil,block=false,crouch=false,cooldown=0,combo=0,comboTimer=0,flash=0,walk=0}end
 remaining=60;phase='fight';freeze=0;intermission=0;acc=0;input={left=false,right=false,down=false,block=false,light=0,heavy=0,special=0,jump=false}
end
local function restart()round=1;wins={0,0};tick=0;resetRound()end
local function finish(winner)
 if winner>0 then wins[winner]=wins[winner]+1 end
 if wins[1]>=2 or wins[2]>=2 then phase=winner==1 and 'KEQING WINS MATCH' or 'DILUC WINS MATCH' else phase=winner==0 and 'DRAW ROUND' or (winner==1 and 'KEQING WINS ROUND' or 'DILUC WINS ROUND') end
 intermission=150;print('ROUND_END '..phase)
end
local function hit(i,j)
 local a,b=f[i],f[j];local atk=a.attack;local s=specs[i][atk.kind]
 if atk.hit or b.hp<=0 or math.abs(b.y-a.y)>75 then return end
 if s.height=='low' and b.y>20 then return end
 local distance=(b.x-a.x)*a.face
 if distance<0 or distance>s.range+20 then return end
 atk.hit=true
 local blocked=b.block and b.y==0 and b.face==-a.face and b.stun<=0 and not b.attack
 if s.height=='low' and not b.crouch then blocked=false end
 if s.height=='high' and b.crouch then blocked=false end
 local damage=blocked and math.max(1,math.floor(s.damage*.15)) or s.damage
 b.hp=math.max(0,b.hp-damage);b.stun=blocked and 8 or s.stun;b.flash=blocked and 0 or 7;b.attack=nil;b.x=clamp(b.x+a.face*(blocked and 10 or s.push),-535,535)
 freeze=blocked and 2 or 4;print((blocked and 'BLOCK' or 'HIT')..' '..i..'>'..j..' damage='..damage..' move='..atk.kind)
end
local function advance(i)
 local a=f[i]
 if a.stun>0 then a.stun=a.stun-1 end
 if a.flash>0 then a.flash=a.flash-1 end
 if a.cooldown>0 then a.cooldown=a.cooldown-1 end
 if a.comboTimer>0 then a.comboTimer=a.comboTimer-1 else a.combo=0 end
 if a.y>0 or a.vy>0 then a.y=a.y+a.vy/60;a.vy=a.vy-1100/60;if a.y<=0 then a.y=0;a.vy=0 end end
 if a.attack then
  local atk=a.attack;local s=specs[i][atk.kind];atk.t=atk.t+1
  if atk.t>=s.startup and atk.t<s.startup+s.active then hit(i,3-i)end
  if atk.t>=s.startup+s.active+s.recovery then a.attack=nil;a.comboTimer=24 end
 end
end
local function step()
 tick=tick+1
 if phase~='fight' then
  if wins[1]<2 and wins[2]<2 then intermission=intermission-1;if intermission<=0 then round=round+1;resetRound()end end;return
 end
 if freeze>0 then freeze=freeze-1;return end
 remaining=math.max(0,remaining-1/60)
 for i=1,2 do if not f[i].attack and f[i].stun<=0 then f[i].face=f[3-i].x>=f[i].x and 1 or -1 end end
 local a,b=f[1],f[2]
 input.light=math.max(0,input.light-1);input.heavy=math.max(0,input.heavy-1);input.special=math.max(0,input.special-1)
 if ready(1) then
  a.crouch=input.down and a.y==0
  a.block=input.block and a.y==0
  if input.special>0 and startAttack(1,'special')then input.special=0 elseif input.heavy>0 and startAttack(1,'heavy')then input.heavy=0 elseif input.light>0 and startAttack(1,a.crouch and 'low' or 'light')then input.light=0 end
  if not a.attack and not a.block and not a.crouch then local move=(input.right and 1 or 0)-(input.left and 1 or 0);a.x=clamp(a.x+move*specs[1].speed/60,-535,535);if move~=0 then a.walk=a.walk+.2 end end
  if input.jump and a.y==0 and not a.block and not a.attack then a.vy=465 end
 end
 input.jump=false
 if aiEnabled and ready(2) then
  local dist=math.abs(a.x-b.x);b.block=false;b.crouch=false
  if a.attack and dist<170 and tick%90<50 and b.y==0 then b.block=true;b.crouch=specs[1][a.attack.kind].height=='low'
  elseif b.cooldown<=0 and dist<250 and tick%100==0 then startAttack(2,'special')
  elseif dist>124 then b.x=clamp(b.x+b.face*specs[2].speed/60,-535,535);b.walk=b.walk+.16
  elseif tick%35==0 then startAttack(2,tick%105==0 and 'low' or (tick%70==0 and 'heavy' or 'light'))end
 end
 for i=1,2 do local c=f[i];if c.attack and c.attack.kind=='special' then local s=specs[i].special;if s.dash and c.attack.t>=s.startup-4 and c.attack.t<s.startup+s.active then c.x=clamp(c.x+c.face*s.dash/60,-535,535)end end end
 -- Ground pushboxes: neither fighter may overlap or swap sides while grounded.
 local gap=b.x-a.x
 if math.abs(gap)<50 and math.abs(a.y-b.y)<75 then local direction=gap>=0 and 1 or -1;local push=(50-math.abs(gap))/2;a.x=clamp(a.x-direction*push,-535,535);b.x=clamp(b.x+direction*push,-535,535)end
 advance(1);advance(2)
 if a.hp<=0 or b.hp<=0 or remaining<=0 then finish(a.hp==b.hp and 0 or (a.hp>b.hp and 1 or 2))end
end
local function draw()
 for i=1,2 do
  local a,art=f[i],actors[i]:FindChild('Art')
  actors[i]:SetAnchoredPosition(a.x,-155+a.y);art:SetLocalScale(a.face,a.crouch and .60 or 1,1)
  local swing=0
  if a.attack then local s=specs[i][a.attack.kind];swing=a.attack.t<s.startup and -35 or (a.attack.t<s.startup+s.active and 0 or 20);if a.attack.kind=='low' then swing=-12 end end
  art:FindChild('Sword'):SetLocalRotation(0,0,swing);art:FindChild('Arm'):SetLocalRotation(0,0,swing*.4)
  local gait=math.sin(a.walk)*13;art:FindChild('BackLeg'):SetLocalRotation(0,0,gait);art:FindChild('FrontLeg'):SetLocalRotation(0,0,-gait)
  actors[i]:FindChild('Flash'):SetVisible(a.flash>0);actors[i]:FindChild('GuardVisual'):SetVisible(a.block);actors[i]:FindChild('GuardVisual'):SetAnchoredPosition(a.face*46,a.crouch and 62 or 115)
  actors[i]:FindChild('Hitbox'):SetVisible(a.attack~=nil and a.attack.hit);actors[i]:FindChild('Hitbox'):SetAnchoredPosition(a.face*110,a.crouch and 45 or 120)
  local fx=actors[i]:FindChild('SpecialFx');fx:SetLocalScale(a.face,1,1);fx:SetVisible(a.attack~=nil and a.attack.kind=='special');if a.attack and a.attack.kind=='special' then fx:SetAnchoredPosition(a.face*100,95)end
  hpBars[i]:SetSizeDelta(math.max(1,480*a.hp/100),19);hpBars[i]:SetAnchoredPosition((i==1 and -565 or 565)+(i==1 and 1 or -1)*240*a.hp/100,264)
 end
 timerText.text=tostring(math.ceil(remaining));status.text=phase=='fight' and ('ROUND '..round..' | '..wins[1]..' - '..wins[2]) or phase
 stats.text='HP '..f[1].hp..' / '..f[2].hp..' | '..(f[1].attack and f[1].attack.kind or (f[1].block and (f[1].crouch and 'LOW GUARD' or 'HIGH GUARD') or 'READY'))..' | '..(f[2].attack and f[2].attack.kind or (f[2].block and 'GUARD' or 'AI'))..' | E CD '..math.ceil(f[1].cooldown/60)..' / '..math.ceil(f[2].cooldown/60)
end
function OnInit()
 root=script.object;actors={root:FindChild('Keqing'),root:FindChild('Diluc')};hpBars={root:FindChild('Hp1'),root:FindChild('Hp2')};status=root:FindChild('Status');timerText=root:FindChild('Timer');stats=root:FindChild('Stats');restart();draw()
end
local function bind(name,callback)root:AddKeyEventListener(Enum.KeyEventType[name],function()callback();return true end)end
function OnStart()
 bind('KeyboardMoveLeftKeyDown',function()input.left=true end);bind('KeyboardMoveLeftKeyUp',function()input.left=false end)
 bind('KeyboardMoveRightKeyDown',function()input.right=true end);bind('KeyboardMoveRightKeyUp',function()input.right=false end)
 bind('KeyboardJumpKeyDown',function()input.jump=true end)
 bind('KeyboardMoveBackwardKeyDown',function()input.down=true end);bind('KeyboardMoveBackwardKeyUp',function()input.down=false end)
 bind('KeyboardCharacterSkill1KeyDown',function()input.special=12 end)
 bind('KeyboardCraftspersonKey19Down',function()input.light=12 end)
 bind('KeyboardCraftspersonKey20Down',function()input.heavy=12 end)
 bind('KeyboardCraftspersonKey21Down',function()input.block=true end);bind('KeyboardCraftspersonKey21Up',function()input.block=false end)
 bind('KeyboardCharacterSkill3KeyDown',restart)
 for _,entry in ipairs({{'Left','left'},{'Right','right'},{'Down','down'},{'Block','block'}})do
  local c,k=root:FindChild(entry[1]),entry[2]
  c:AddCursorEventListener(Enum.CursorEventType.CursorDown,function()input[k]=true end)
  c:AddCursorEventListener(Enum.CursorEventType.CursorUp,function()input[k]=false end)
  c:AddCursorEventListener(Enum.CursorEventType.CursorExit,function()input[k]=false end)
 end
 for _,entry in ipairs({{'Light',function()input.light=12 end},{'Heavy',function()input.heavy=12 end},{'Special',function()input.special=12 end},{'Jump',function()input.jump=true end},{'Restart',restart}})do root:FindChild(entry[1]):AddCursorEventListener(Enum.CursorEventType.CursorClick,entry[2])end
 script:EnableUpdate(true)
end
function OnDisable()input.left=false;input.right=false;input.down=false;input.block=false end
function OnUpdate(dt)
 acc=acc+math.min(dt,.1);local n=0;while acc>=1/60 and n<6 do acc=acc-1/60;n=n+1;step()end;draw()
end
