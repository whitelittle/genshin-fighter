__loaders['gf_scene_update_notice']=function()
local G=require('gf_gfx')
local UI=require('gf_ui')
local Data=require('gf_update_notice_data')
local S={};S.__index=S
function S.new(app)
 local self=setmetatable({app=app,t=0,items={}},S)
 app.initialNoticeShown=true
 app.env.initialNoticeShown=true
 for _,entry in ipairs(Data.updates)do
  if entry.confirmed and not entry.candidate then self.items[#self.items+1]=entry end
 end
 self.L=G.layer(app.layers.hud);app.input:clearUI()
 self.menu=UI.menu(app,app.layers.ui,{{id='continue',label='进入游戏'}},{x=0,y=-app.H/2+85,w=430,h=60,size=28,onPick=function()self:confirm()end,onBack=function()self:confirm()end})
 return self
end
function S:confirm()
 if self.t<.25 or self.app.trans then return end
 self.app:travel('title')
end
function S:tick()self.t=self.t+1/60;self.menu:input(self.app.input:menu())end
function S:draw()
 local app=self.app;local W,H=app.W,app.H;local L=self.L;L:begin()
 app:cover(L,UI.NAVY,1)
 UI.rrect(L,0,0,math.min(W-80,1420),H-45,16,UI.NAVY2,.9)
 L:label('更新公告',0,H/2-72,W-120,65,42,UI.GOLD,'c')
 L:label(Data.stage,0,H/2-146,W-160,55,25,UI.CREAM,'c')
 L:label(Data.nextGoal,0,H/2-198,W-160,55,25,UI.GOLD,'c')
 local left=-math.min(W-180,1220)/2;local width=math.min(W-180,1220)
 L:label('已确认更新记录',0,H/2-262,width,44,28,UI.WHITE,'c')
 local top=H/2-315
 L:rect(0,top,width,42,UI.SLATE,.9)
 local sourceW,itemW=180,300
 local bottom=top-21-#self.items*112
 for _,x in ipairs({left,left+sourceW,left+sourceW+itemW,left+width})do
  L:rect(x,(top+21+bottom)/2,2,top+21-bottom,UI.GOLD,.65)
 end
 L:rect(0,top+21,width,2,UI.GOLD,.65)
 L:rect(0,top-21,width,2,UI.GOLD,.65)
 L:label('日期',left+sourceW/2,top,sourceW,35,22,UI.GOLD,'c')
 L:label('更新项目',left+sourceW+itemW/2,top,itemW,35,22,UI.GOLD,'c')
 L:label('更新内容',left+sourceW+itemW+(width-sourceW-itemW)/2,top,width-sourceW-itemW,35,22,UI.GOLD,'c')
 for i,entry in ipairs(self.items)do
  local y=top-77-(i-1)*112
  L:label(entry.date,left+sourceW/2,y,sourceW-12,65,21,UI.GOLD,'c')
  L:label(entry.title,left+sourceW+itemW/2,y,itemW-18,65,23,UI.CREAM,'c')
  local textW=width-sourceW-itemW-28;local chars={}
  for _,code in utf8.codes(entry.detail)do chars[#chars+1]=utf8.char(code)end
  local n=math.max(12,math.floor(textW/22));local lines={}
  for j=1,#chars,n do lines[#lines+1]=table.concat(chars,'',j,math.min(j+n-1,#chars))end
  L:label(table.concat(lines,'\n'),left+sourceW+itemW+14+textW/2,y,textW,90,22,UI.DIM,'l')
  L:rect(0,y-56,width,2,UI.GOLD,.65)
 end
 L:label('仅列已确认更新；开发中的内容暂不收录。',0,-H/2+154,W-120,35,19,UI.GOLD,'c')
 L:finish();self.menu:draw()
end
function S:exit()self.menu:free();self.L:free()end
return S
end
