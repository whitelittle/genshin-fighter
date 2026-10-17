__loaders['gf_app_recovery']=function()
local G=require('gf_gfx');local UI=require('gf_ui')
return function(App)
function App:initRecovery(previous)
    if previous then
        self.recovery=previous;previous.menu.app=self
        previous.action=nil;previous.reset=nil;previous.message=nil
        previous.root:on(false)
        return
    end
    local r={root=G.group(G.root)};self.recovery=r
    r.L=G.layer(r.root)
    r.menu=UI.menu(self,r.root,{{id='restart',label='重启游戏'},{id='quit',label='退出游戏'}},
        {parent=r.root,x=-390,y=-50,w=560,h=72,gap=20,size=34,onPick=function(id)
            if not r.action and not r.reset then r.action=id end
        end})
    -- Reserve all graphics before scene construction / pool exhaustion.
    self:drawRecovery();r.menu.t=20;r.menu:draw();r.root:on(false)
    self.input:clearUI()
end
function App:drawRecovery()
    local r=self.recovery;local cw,ch=self.env.game.GetUICanvasSize()
    if type(cw)~='number' or type(ch)~='number' or cw<=0 or ch<=0 then cw,ch=1600,900 end
    local scale=math.min(cw/1600,ch/900)
    self.cw,self.ch,self.s=cw,ch,scale
    r.root:scale(scale):front()
    local L=r.L;L:begin()
    UI.slab(L,0,0,cw/scale+320,ch/scale+320,UI.NAVY,1,0)
    UI.slab(L,-690,0,720,ch/scale+360,UI.NAVY2,1,-UI.SLANT)
    L:label('游戏运行中断',-220,250,900,76,50,UI.CREAM,'l')
    L:label('请先截图反馈，再选择重启或退出',-220,185,900,46,24,UI.GOLD,'l')
    L:label((r.message or ''):sub(1,400),0,90,1400,100,20,UI.GREY,'l')
    local status=r.reset and '正在清理本局并重启…' or self.quitPending and
        (self.quitPending.error and '退出请求发送失败，可再次尝试' or self.quitPending.elapsed>5 and '仍在等待退出确认，请使用千星系统退出入口' or '正在请求退出游戏…') or
        '重启将回到标题页，当前对局不会继续'
    L:label(status,-100,-245,1140,50,24,UI.GOLD,'l')
    L:finish();r.menu:draw()
end
function App:enterRecovery(message)
    local r=self.recovery;r.message=tostring(message);r.action=nil;r.reset=nil
    -- Stop network traffic without touching a potentially broken scene.
    if self.net and self.net.io.stop then pcall(self.net.io.stop) end
    if self.teamSelectionIO then pcall(self.teamSelectionIO.stop) end
    self.input:clearUI();self.input.held={};self.input.rep={}
    for _,p in ipairs(self.input.pads) do p.held=0;p.prev=0;p.counts={};p.touch=0;p.pulse=0;p.stick=0 end
    self.view:on(false);self.canvasBacking:on(false)
    self.env.host:SetVisible(false)
    r.root:on(true);r.menu.sel=1;r.menu:bind()
    -- Allow coordinate-free native click/up events on these explicit controls.
    for _,b in ipairs(r.menu.areas) do
        if b then
            local armed=false
            local click=b.handlers.click
            local function pick() if not armed then armed=true;click() end end
            b.handlers={coordinateFree=true,down=function()armed=false end,up=pick,click=function()if not armed then armed=true;click() end end}
            b.node.handlers=b.handlers
        end
    end
    self:drawRecovery()
end
function App:updateRecovery(dt)
    if self.closed then return end
    local r=self.recovery
    if r.action=='quit' then
        r.action=nil
        if not self.quitPending then
            self:quitGame();r.menu:bind();r.menu.items[1].disabled=true
        else self.quitPending.nextSend=self.quitPending.elapsed end
    elseif r.action=='restart' and not self.quitPending then
        r.action=nil;self.input:clearUI()
        r.reset=G.beginRecovery({self.view,self.canvasBacking})
    end
    if self.quitPending then self:serviceExit(dt) end
    if r.reset then
        if G.advanceRecovery(r.reset,128) then
            local env={};for k,v in pairs(self.env) do env[k]=v end
            env.firstScene='title';env.firstArgs=nil;env.recoveryInput=self.input;env.recoveryUI=r
            local nextApp=App.new(env)
            nextApp.save=self.save;nextApp.settings=self.settings
            nextApp.recovery.root:on(false)
            return nextApp
        end
    elseif not self.quitPending then
        self.input:poll();r.menu:input(self.input:menu())
    end
    self:drawRecovery()
end
end
end
