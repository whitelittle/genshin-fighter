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
        if a=='diagnostic' or a=='debug' then self.diagOpen=not self.diagOpen
        elseif a=='back' then
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
    local status=not o and '暂时无法连接' or not o.slot and '正在连接…' or '等待另一位玩家进入'
    L:label(status,-W/2+400,65,640,60,26,UI.WHITE,'c')
    L:label('双方连接后自动进入选人',-W/2+400,8,640,40,20,UI.GREY,'c')
    L:label('请让另一位玩家也选择联机对决',-W/2+400,-45,640,40,20,UI.GOLD,'c')
    local d=o and o.io.diag
    if d and self.diagOpen then
        L:label(('握手发送 %d · 席位回包 %d'):format(d.hello,d.seat),-W/2+400,-105,700,44,20,UI.WHITE,'c')
        L:label(('消息发送 %d · 接收 %d · 有效 %d'):format(d.sent,d.received,d.accepted),-W/2+400,-150,700,44,20,UI.GREY,'c')
        local hint=d.error and ('发送失败：'..d.error) or
            (d.hello>=3 and d.seat==0 and '未收到席位：核对节点图挂载、运行及实际引用的 GFV2 信号名') or
            (d.seat>0 and d.received==0 and '已有席位：等待另一端进入联机；若双方都在此页，检查转发和实体变量') or
            (d.rejected>0 and ('消息被拒绝：'..(d.rejectReason or '未知'))) or ''
        L:label(hint,-W/2+430,-205,760,70,18,UI.GOLD,'c')
    end
    UI.prompt(L,-W/2+140,-H/2+34,'F9',self.diagOpen and '收起诊断' or '诊断',1,'diagnostic')
    UI.prompt(L,W/2-160,-H/2+34,'K','返回',1,'back')
    L:finish()
end
function S:exit() self.L:free(); self.B:free() end
return S
end
