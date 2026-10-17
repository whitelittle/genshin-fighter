__loaders['gf_app_exit']=function()
local G=require('gf_gfx');local UI=require('gf_ui')
local Signals=require('gf_signal_names')
return function(App)
function App:initExit()
    if self.env.exitState then self.env.exitState.app=self;return end
    local owner={app=self};self.env.exitState=owner
    self.env.script:RegisterServerSignalHandler(Signals.resolve('GF3Close'),function()
        local self=owner.app
        self.closed=true;self.quitPending=nil
        if self.net and self.net.io.stop then self.net.io.stop() end
        if self.teamSelectionIO then self.teamSelectionIO.stop() end
        self.input:clearUI()
        self.env.root:SetVisible(false);self.env.root:SetActive(false)
        self.env.script:EnableUpdate(false)
    end)
end
function App:quitGame()
    if self.closed or self.quitPending then return end
    if self.net and self.net.io.stop then self.net.io.stop() end
    if self.teamSelectionIO then self.teamSelectionIO.stop() end
    self.quitPending={elapsed=0,nextSend=0};self.input:clearUI()
end
function App:serviceExit(dt)
    local q=self.quitPending;if not q then return false end
    q.elapsed=q.elapsed+math.max(0,dt or 0)
    if q.elapsed>=q.nextSend then
        q.nextSend=q.elapsed+.75
        local ok,err=pcall(function()self.env.game.ServerSignal(Signals.resolve('GF3Quit')):SendSignal()end)
        q.error=not ok and tostring(err) or nil
    end
    return true
end
function App:advanceExit(dt)
    if not self:serviceExit(dt) or self.closed then return self.closed or false end
    local q=self.quitPending
    self.exitL=self.exitL or G.layer(self.layers.curtain);local L=self.exitL;L:begin()
    self:cover(L,UI.NAVY,1)
    L:label('正在结算并退出',0,35,700,70,40,UI.CREAM,'c')
    if q.error or q.elapsed>5 then L:label(q.error and '退出信号发送失败，请检查 GF3Quit' or '等待服务器关闭确认，请检查退出节点挂载',0,-35,1000,50,22,UI.GOLD,'c') end
    L:finish();return true
end
end
end
