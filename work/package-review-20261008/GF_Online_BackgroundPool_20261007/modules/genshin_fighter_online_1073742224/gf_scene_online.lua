__loaders['gf_scene_online'] = function()
local G=require('gf_gfx')
local UI=require('gf_ui')
local O=require('gf_online')
local S={}; S.__index=S
function S.new(app)
    local self=setmetatable({app=app,t=0,L=G.layer(app.layers.ui),B=G.layer(app.layers.back)},S)
    self.net=app:netOn()
    if self.net then
        O.leaveMatch(self.net)
        self.net.me.selecting=false
        self.net.host.rounds,self.net.host.time=app.settings.rounds,app.settings.time
    end
    return self
end
function S:tick()
    self.t=self.t+1/60
    local o=self.net
    for _,a in ipairs(self.app.input:menu()) do
        if a=='back' then
            if o and o.io.stop then o.io.stop() end
            self.app.net=nil
            self.app:travel('menu',{sel=2}); return
        end
    end
    if o and O.opponent(o) and not self.left and not self.app.trans then
        self.left=true
        self.app.audio:play(self.app.audio.ID.ok)
        self.app:travel('select',{mode='online',online=true})
    end
end
function S:draw()
    local app=self.app; local W,H=app.W,app.H
    local B=self.B; B:begin()
    B:rect(0,0,W+40,H+40,UI.NAVY,1)
    UI.leftPanel(B,W,H,1,UI.GOLD,1)
    UI.constellation(B,W/4,0,180,self.t*12,UI.GOLD,.7)
    B:finish()
    local L=self.L; L:begin()
    UI.screenTitle(L,W,H,'联机对决',UI.track('ONLINE VERSUS'),1)
    local o=self.net
    local status=not o and '联机接口不可用' or not o.slot and '正在握手 · 等待服务器分配席位' or '席位已分配 · 等待另一位玩家进入'
    L:label(status,-W/2+400,65,640,60,26,UI.WHITE,'c')
    L:label('双方连接后自动进入选人',-W/2+400,8,640,40,20,UI.GREY,'c')
    L:label(o and o.slot and ('你的席位：'..o.slot) or '请确认已挂载 V2 联机服务器节点图',-W/2+400,-45,640,40,20,UI.GOLD,'c')
    UI.prompt(L,W/2-160,-H/2+34,'K','返回',1,'back')
    L:finish()
end
function S:exit() self.L:free(); self.B:free() end
return S
end
