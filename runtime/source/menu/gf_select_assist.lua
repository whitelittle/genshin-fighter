__loaders['gf_select_assist']=function()
local UI=require('gf_ui')
return function(S)
 local new,confirm,draw=S.new,S.confirm,S.draw
 function S.new(app,args)
  local self=new(app,args)
  if args and args.teamPreview then return self end
  self.mainChoice={};self.assistChoice={};self.pickCount={0,0}
  return self
 end
 function S:confirm(p)
  if self.teams then return confirm(self,p) end
  local c=self.roster[self.cur[p]]
  if c.selectionOnly then self.notice='此角色暂供选人预览';return end
  if self.pickCount[p]==0 then
   self.mainChoice[p]=self.cur[p];self.pickCount[p]=1
   self.focused[p]=false;self.shown[p]=nil
   self.notice='第2选：选择协同角色'
   self.app.audio:play(self.app.audio.ID.okBig)
   if self.net then self.net.me.char=self.mainChoice[p] end
   return
  end
  if self.pickCount[p]==1 then
   if self.mainChoice[p]==self.cur[p] then self.notice='协同角色需与主角色不同';return end
   self.assistChoice[p]=self.cur[p];self.pickCount[p]=2
   if self.net then self.net.me.assist=self.assistChoice[p] end
  end
  return confirm(self,p)
 end
 function S:undoAssistPick()
  local p=self:activePlayer() or (self.done[2] and 2 or 1)
  if (self.pickCount[p] or 0)==0 and p==2 then p=1 end
  if (self.pickCount[p] or 0)==0 then return false end
  self.done[p]=false
  if self.pickCount[p]==2 then
   self.cur[p]=self.assistChoice[p];self.assistChoice[p]=nil;self.pickCount[p]=1
  else self.cur[p]=self.mainChoice[p];self.mainChoice[p]=nil;self.pickCount[p]=0 end
  if self.net then self.net.me.ready=false;self.net.me.assist=0 end
  self.focused[p]=true;self.shown[p]=nil;self.phase='chars';return true
 end
 function S:draw()
  draw(self)
  if self.teams then return end
 end
end
end
