import {readFileSync,writeFileSync} from 'node:fs';
const visual=`
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
`;
for(const online of [false,true]){
 let s=readFileSync(online?'work/fighter-online.lua':'work/fighter.lua','utf8');
 s=s.replace('local input=',"local stage,roleChoice=1,{1,2}\nlocal input=");
 s=s.replace('local commands={',"local commands={{sequence={2,3,6,2,3,6},button='heavy',move='super'},");
 s=s.replace('tick-event.t>24','tick-event.t>(#sequence>3 and 42 or 24)');
 s=s.replace('specs[2].rising={startup=12,active=8,recovery=38,range=125,heightRange=190,damage=18,stun=30,push=32}',`specs[2].rising={startup=12,active=8,recovery=38,range=125,heightRange=190,damage=18,stun=30,push=32}
specs[1].super={startup=16,active=10,recovery=38,range=310,heightRange=220,damage=38,stun=40,push=65}
specs[2].super={startup=24,active=12,recovery=45,range=370,heightRange=220,damage=44,stun=44,push=75}
moveNames[1].super='天街巡游';moveNames[2].super='黎明'
specs[1].overhead={startup=21,active=4,recovery=26,range=140,damage=18,stun=26,push=42,height='high'}
specs[2].overhead={startup=29,active=5,recovery=32,range=175,damage=24,stun=32,push=50,height='high'}
moveNames[1].overhead='上段斩';moveNames[2].overhead='上段斩'
-- Neutral heavy is mid. Forward + heavy is overhead; down + light is low.
specs[1].heavy.height=nil;specs[2].heavy.height=nil`);
 s=s.replace(/specs\[i\]/g,'specs[f[i].role]').replace(/specs\[1\]\[a.attack.kind\]/g,'specs[a.role][a.attack.kind]').replace('specs[1].speed','specs[a.role].speed').replace('specs[2].speed','specs[b.role].speed');
 s=s.replace('moveNames[1][f[1].attack.kind]','moveNames[f[1].role][f[1].attack.kind]').replace('moveNames[2][f[2].attack.kind]','moveNames[f[2].role][f[2].attack.kind]');
 s=s.replace("or kind=='rising'","or kind=='rising' or kind=='super' or kind=='overhead'");
 s=s.replace("local cancel=canCancel(i,kind)",`if kind=='heavy' then
 local c=${online?'controls[i] and controls[i].input or input':'i==1 and input or {}'}
 if (a.face==1 and c.right) or (a.face==-1 and c.left) then kind='overhead' end
end
local cancel=canCancel(i,kind)`);
 s=s.replace("a.chainCount=cancel and", "if kind=='super' and (a.meter<100 or a.y>0) then return false end\n if kind=='super' then a.meter=a.meter-100;print('SUPER '..i)end\n a.chainCount=cancel and");
 s=s.replace('hp=100,face=', 'hp=100,role=roleChoice[i],meter=0,face=');
 s=s.replace('b.hp=math.max(0,b.hp-damage);',"a.meter=math.min(100,a.meter+(blocked and 4 or damage*.9));b.meter=math.min(100,b.meter+damage*1.2);\n b.hp=math.max(0,b.hp-damage);");
 s=s.replace(/atk.kind=='heavy' or atk.kind=='special'/g,"atk.kind=='heavy' or atk.kind=='overhead' or atk.kind=='super' or atk.kind=='special'");
 s=s.replace("if freeze>0 then freeze=freeze-1;return end","if freeze>0 then freeze=freeze-1;return end\n for i=1,2 do f[i].meter=math.min(100,f[i].meter+.045)end");
 // The same role-specific decision logic runs regardless of the selected role.
 s=s.replace("elseif dist<250 and tick%100==0 then", "elseif b.meter>=100 and dist<330 and tick%90==0 then startAttack(2,'super')\n  elseif dist<250 and tick%(b.role==1 and 80 or 100)==0 then");
 s=s.replace('elseif dist>124 then','elseif dist>(b.role==1 and 98 or 124) then');
 s=s.replace("local function draw()",visual+"\nlocal function draw()");
 s=s.replace("  art:FindChild('Sword'):SetLocalRotation(0,0,swing);art:FindChild('Arm'):SetLocalRotation(0,0,swing*.4)\n  art:FindChild('Sword'):SetVisible(a.down<=0);art:FindChild('Arm'):SetVisible(a.down<=0)\n  local gait=math.sin(a.walk)*13;art:FindChild('BackLeg'):SetLocalRotation(0,0,gait);art:FindChild('FrontLeg'):SetLocalRotation(0,0,-gait)","  updateSprite(i)");
 s=s.replace("a.attack.kind=='special' or a.attack.kind=='rising'","a.attack.kind=='special' or a.attack.kind=='rising' or a.attack.kind=='super'");
 s=s.replace("SetVisible(a.attack~=nil and a.attack.hit)","SetVisible(false)");
 s=s.replace(" timerText.text=", " drawStage()\n timerText.text=");
 s=s.replace(" | 必杀 236+J/K / 挑飞 623+K'"," | 必杀 236+J/K / 挑飞 623+K / 超必杀 236236+K'");
 s=s.replace("phaseNames[phase]", "(phase=='DRAW ROUND' and '本回合平局' or (({'刻晴','迪卢克'})[f[(wins[1]>=2 or phase=='KEQING WINS ROUND') and 1 or 2].role]..((wins[1]>=2 or wins[2]>=2) and '赢得比赛' or '赢得本回合')))");
 const extraSolo=`
 for _,e in ipairs({{'RoleKeqing',1},{'RoleDiluc',2}})do root:FindChild(e[1]):AddCursorEventListener(Enum.CursorEventType.CursorClick,function()roleChoice={e[2],3-e[2]};spriteCache={};restart();draw()end)end
 for n=1,3 do root:FindChild('SelectStage'..n):AddCursorEventListener(Enum.CursorEventType.CursorClick,function()stage=n;draw()end)end
`;
 const extraOnline=`
 for _,e in ipairs({{'RoleKeqing',1},{'RoleDiluc',2}})do root:FindChild(e[1]):AddCursorEventListener(Enum.CursorEventType.CursorClick,function()sendInput('role',e[2])end)end
 for n=1,3 do root:FindChild('SelectStage'..n):AddCursorEventListener(Enum.CursorEventType.CursorClick,function()sendInput('stage',n)end)end
`;
 // Eight-way touch stick: down/enter events use the same absolute direction history as keyboard.
 const extraStick=`
 local stickHeld=false
 local function stick(d)
  local x=(d==1 or d==4 or d==7) and -1 or ((d==3 or d==6 or d==9) and 1 or 0)
  local down=d<=3
  ${online?"sendInput('stick',d)":"input.left=x<0;input.right=x>0;input.down=down;recordDirection();if d>=7 then input.jump=true end"}
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
`;
 s=s.replace(' script:EnableUpdate(true)',(online?extraOnline:extraSolo)+extraStick+'\n script:EnableUpdate(true)');
 if(online){
  s=s.replace("'flash','walk'","'flash','walk','role','meter'");
  s=s.replace('add(intermission)','add(intermission);add(stage)');
  s=s.replace('#values~=57','#values~=62');
  s=s.replace('freeze=num();intermission=num()','freeze=num();intermission=num();stage=num()');
  s=s.replace(" if event=='restart' then", " if event=='stage' then stage=clamp(value,1,3);return end\n if event=='role' then roleChoice[player]=clamp(value,1,2);spriteCache={};restart();return end\n if event=='restart' then");
  s=s.replace("  if event=='left'", "  if event=='stick' then input.left=(value==1 or value==4 or value==7);input.right=(value==3 or value==6 or value==9);input.down=value<=3;recordDirection();if value>=7 then input.jump=true end\n  elseif event=='left'");
 }
 writeFileSync(online?'work/demo-online.lua':'work/demo-solo.lua',s);
}
