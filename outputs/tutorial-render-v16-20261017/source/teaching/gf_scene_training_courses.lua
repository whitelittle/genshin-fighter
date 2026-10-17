__loaders['gf_scene_training_courses']=function()
local G=require('gf_gfx')
local UI=require('gf_ui')
local Courses=require('gf_training_courses')
local S={};S.__index=S
function S.new(app,args)
 local self=setmetatable({app=app,page=args and args.page or 'main'},S)
 self.L=G.layer(app.layers.hud)
 self:build();return self
end
function S:build()
 if self.menu then self.menu:free() end
 self.app.input:clearUI()
 self.items={}
 for _,course in ipairs(Courses[self.page])do
  local complete=self.app.trainingCompleted and self.app.trainingCompleted[course.id]
  self.items[#self.items+1]={id=course.id,label=(complete and '完成 · ' or '')..course.label,course=course}
 end
 self.items[#self.items+1]={id='back',label=self.page=='main' and '返回主菜单' or '返回课程目录'}
 local app=self.app
 self.menu=UI.menu(app,app.layers.ui,self.items,{x=-app.W/2+350,y=app.H/2-175,w=590,h=44,gap=5,size=25,numbers=true,
  onPick=function(id)self:pick(id)end,onBack=function()self:pick('back')end})
end
function S:pick(id)
 local app=self.app
 if id=='back' then
  if self.detail then self.detail=nil;self:build()
  elseif self.page=='elements' then self.page='main';self:build()
  else app:travel('menu') end
  return
 end
 if self.detail then return end
 if id=='elements' then self.page='elements';self:build();return end
 for _,course in ipairs(Courses[self.page])do
  if course.id==id then
   if course.available then app:travel('fight',{chars={'lumine','lawachurl'},mode='training',tutorial=true,cpu={false,false},seed=21,lessonCourse=id})
   else
    self.detail=course;self.menu:free();self.menu=nil;app.input:clearUI()
    self.menu=UI.menu(app,app.layers.ui,{{id='back',label='返回课程目录'}},{x=0,y=-app.H/2+110,w=480,h=60,size=27,onPick=function()self:pick('back')end,onBack=function()self:pick('back')end})
   end
   return
  end
 end
end
function S:tick()self.menu:input(self.app.input:menu())end
function S:draw()
 local app=self.app;local L=self.L;L:begin()
 app:cover(L,UI.NAVY,1)
 UI.screenTitle(L,app.W,app.H,'派蒙的训练课堂',self.page=='elements' and '七元素课程' or '选择一课，慢慢练习',1)
 local course=self.detail or (self.items[self.menu.sel] and self.items[self.menu.sel].course)
 local x=self.detail and 0 or app.W/2-390
 if course then
  UI.rrect(L,x,100,690,310,14,UI.NAVY2,1)
  L:label(course.label,x,210,640,48,34,UI.GOLD,'c')
  local status=course.status or '待接入 · 七元素技能与反应教学'
  L:label(status,x,145,640,60,23,UI.CREAM,'c')
  local chars={};for _,code in utf8.codes(course.desc)do chars[#chars+1]=utf8.char(code)end
  local lines={};for i=1,#chars,24 do lines[#lines+1]=table.concat(chars,'',i,math.min(i+23,#chars))end
  L:label(table.concat(lines,'\n'),x,55,640,110,23,UI.CREAM,'c')
  if self.detail then L:label('派蒙：这课还在准备，我们先练已经开放的基础吧。',x,-100,980,65,25,UI.GOLD,'c') end
 end
 local dev=app.input:device()
 local p=app.input.controllerLayout
 local hint=dev=='touch' and '点击课程选择' or dev=='pad' and '左摇杆选择 · '..p.confirm..' 确认 · '..p.back..' 返回' or 'W/S 选择 · J/空格确认 · K返回'
 L:label(hint,0,-app.H/2+35,1200,36,21,UI.GOLD,'c')
 L:finish();self.menu:draw()
end
function S:exit()self.menu:free();self.L:free()end
return S
end
