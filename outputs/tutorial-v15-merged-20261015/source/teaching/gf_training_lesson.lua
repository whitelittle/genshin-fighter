__loaders['gf_training_lesson']=function()
local G=require('gf_gfx')
local UI=require('gf_ui')
local U=require('gf_util')
local T={};T.__index=T
local lessons={
 {goal='向前移动一小段',guide='旅行者，我们先熟悉移动！向丘丘王的方向走一小段吧。',done='没错！走路可以调整距离，先别急着出剑。',kind='forward'},
 {goal='向后退一小段',guide='再试着往后退。保持面对敌人，拉开一点距离。',done='很好！靠近和后退，是控制距离的第一步。',kind='back'},
 {goal='跳起并安全落地',guide='接下来跳一下！落地站稳，就完成这一步啦。',done='落地成功！跳跃之后，也要留意自己什么时候能行动。',kind='jump'},
 {goal='向前冲刺一次',guide='现在试试向前冲刺。它比走路快，适合迅速接近敌人。',done='冲起来啦！不过冲刺不能代替防御，要看好距离哦。',kind='dash'},
 {goal='靠近丘丘王，进入攻击距离',guide='丘丘王暂时不会还手。先靠近它，准备试试手里的剑。',done='这个距离可以试着出剑啦！看清准备、出手和收势。',kind='approach'},
 {goal='用轻击命中丘丘王一次',guide='按轻击攻击它！要真的碰到丘丘王，远处挥空可不算哦。',done='打中了！你看，它受击后会恢复站姿。基础练习完成啦！',kind='hit'},
}
function T.new(scene)
 local self=setmetatable({scene=scene,index=1,pending=0,lastTick=-1},T)
 self.course=scene.args.lessonCourse
 self.lessons=lessons
 if self.course=='movement' then
  self.lessons={lessons[1],lessons[2],lessons[3],lessons[4],{goal='向后撤一步',guide='再试试后撤！保持面对丘丘王，迅速向后挪开。',done='很好！移动练习完成。后撤的时机，我们以后继续打磨。',kind='backdash'}}
 elseif self.course=='attack' then self.lessons={lessons[5],lessons[6]} end
 self.L=G.layer(scene.app.layers.hud)
 local img=require('gf_paimon_training_avatar')
 if not img.bytes then img.bytes=U.rectangleValues(img,U.decodeImage(img));img.d=nil end
 self.avatar=G.bitmap(scene.app.layers.hud);self.avatar:draw(img,'paimon-guide')
 self.avatarImage=img;self:enter(1)
 return self
end
function T:enter(index)
 self.index=index;self.pending=0;self.jumpSeen=false;self.dashSeen=false;self.backdashSeen=false
 local p=self.scene.sim.f[1]
 self.startX=p.x;self.startHits=p.stats.hits;self.lastTick=self.scene.sim.tick
 self.line=self.lessons[index] and self.lessons[index].guide or '做得不错，旅行者！可以重练这一课，回到课程选择，或者留下自由练习。'
 if not self.lessons[index] and self.course then
  local app=self.scene.app;app.trainingCompleted=app.trainingCompleted or {};app.trainingCompleted[self.course]=true
  app.input:clearUI()
  self.completeMenu=UI.menu(app,app.layers.ui,{{id='retry',label='再练一次'},{id='courses',label='选择其他课程'},{id='free',label='自由练习'}},{x=0,y=160,w=480,h=60,gap=12,size=28,
   onPick=function(id)
    if id=='retry' then app:travel('fight',self.scene.args)
    elseif id=='courses' then app:travel('trainingcourses')
    else self.completeMenu:free();self.completeMenu=nil;self.scene:touchControls() end
   end,onBack=function()app:travel('trainingcourses')end})
 end
end
function T:tick()
 local sim=self.scene.sim
 if sim.phase~='fight' or self.lastTick==sim.tick then return end
 self.lastTick=sim.tick
 if self.pending>0 then
  self.pending=self.pending-1
  if self.pending==0 then self:enter(self.index+1) end
  return
 end
 local lesson=self.lessons[self.index];if not lesson then return end
 local p=sim.f[1]
 for _,event in ipairs(sim.events)do
  if event.p==1 and event.type=='jump' then self.jumpSeen=true end
  if event.p==1 and event.type=='dash' and not event.back then self.dashSeen=true end
  if event.p==1 and event.type=='dash' and event.back then self.backdashSeen=true end
 end
 local kind=lesson.kind
 local complete=kind=='forward' and p.x-self.startX>=10000
  or kind=='back' and self.startX-p.x>=8000
  or kind=='jump' and self.jumpSeen and p.y==0 and (p.state=='land' or p.state=='idle')
  or kind=='dash' and self.dashSeen and p.x-self.startX>=5000
  or kind=='backdash' and self.backdashSeen and self.startX-p.x>=3000
  or kind=='approach' and math.abs(p.foe.x-p.x)<=20000
  or kind=='hit' and p.stats.hits>self.startHits
 if complete then self.line=lesson.done;self.pending=120 end
end
function T:draw()
 local app=self.scene.app;local W,H=app.W,app.H;local mobile=app:isMobile();local device=app.input:device()
 local L=self.L;L:begin()
 local lesson=self.lessons[self.index]
 local goal=lesson and lesson.goal or (self.completeMenu and '本课目标已完成' or '教学完成 · 自由练习')
 if self.pending>0 then goal='✓ '..goal end
 local width=math.min(W-60,940)
 UI.rrect(L,0,H/2-58,width,76,12,UI.NAVY,.94)
 L:label(lesson and ('当前目标  '..self.index..'/'..#self.lessons) or '本课完成',0,H/2-38,width-35,28,18,UI.GOLD,'c')
 L:label(goal,0,H/2-71,width-35,34,26,UI.CREAM,'c')
 local panelW=math.min(W-60,1280)
 local y=mobile and H/2-185 or -H/2+112
 UI.rrect(L,0,y,panelW,146,12,UI.NAVY,.95)
 L:rect(0,y+71,panelW-28,2,UI.GOLD,.85)
 local left=-panelW/2
 local avatarSize=248
 local avatarX=math.max(-W/2+avatarSize/2+20,left+20)
 self.avatar.node:pos(avatarX,y-88):scale(avatarSize/self.avatarImage.w,avatarSize/self.avatarImage.w):on(true)
 local textLeft=math.max(left+170,avatarX+avatarSize/2+22)
 L:label('派蒙',textLeft+60,y+44,120,30,25,UI.GOLD,'l')
 -- Explicit UTF-8 wrapping keeps the same readable text in narrow safe areas.
 local textW=panelW-(textLeft-left)-25;local font=mobile and 23 or 25
 local maxChars=math.max(8,math.floor(textW/font));local lines={};local chunk='';local n=0
 for _,code in utf8.codes(self.line)do
  chunk=chunk..utf8.char(code);n=n+1
  if n>=maxChars then lines[#lines+1]=chunk;chunk='';n=0 end
 end
 if chunk~='' then lines[#lines+1]=chunk end
 L:label(table.concat(lines,'\n'),textLeft+textW/2,y-12,textW,88,font,UI.CREAM,'l')
 local keyHints={forward='按住 D 向前走',back='按住 A 向后退',jump='按 W 或空格，跳起后松开',dash='按 U 向前冲刺',backdash='按住后方向，再按 U 后撤',approach='按 A/D 调整距离，靠近后停下',hit='按 J 轻击，真正命中才算完成'}
 local touchHints={forward='摇杆向右推动',back='摇杆向左推动',jump='点一下「跳」，等待落地',dash='点一下「冲」',backdash='摇杆向后推动，同时点「冲」',approach='推动摇杆靠近，进入距离后松开',hit='点一下「轻」，真正命中才算完成'}
 local p=app.input.controllerLayout
 local padHints={forward='左摇杆向前推动',back='左摇杆向后推动',jump='按 '..p.jump..' 跳跃，等待落地',dash='按 '..p.dash..' 向前冲刺',backdash='左摇杆向后，同时按 '..p.dash,approach='左摇杆调整距离，靠近后停下',hit='按 '..p.light..' 轻击，真正命中才算完成'}
 local hints=device=='touch' and touchHints or device=='pad' and padHints or keyHints
 local hint=lesson and hints[lesson.kind] or (device=='touch' and '选择重练、其他课程或自由练习' or device=='pad' and '左摇杆选择 · '..p.confirm..' 确认' or 'W/S 选择 · J确认 · P菜单')
 if self.pending>0 then hint='做得好！马上进入下一项。' end
 L:label(hint,0,mobile and y-93 or y-91,panelW,28,18,UI.GOLD,'c')
 if device=='pad' then L:label('推荐手柄布局 · 平台按键设置需对应',0,y-119,panelW,24,16,UI.DIM,'c') end
 L:finish()
 if self.completeMenu then self.completeMenu:draw() end
end
function T:free()if self.completeMenu then self.completeMenu:free()end;self.avatar:free();self.L:free()end
return T
end
