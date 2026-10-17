__loaders['gf_scene_team_select'] = function()
-- First UI revision: retain the existing roster layout, add numbered player tags only.
local Base=require('gf_scene_select')
local UI=require('gf_ui')
local Art=require('gf_selection_art')
local G=require('gf_gfx')
local T=setmetatable({}, {__index=Base});T.__index=T
local colors={{255,196,92},{98,200,255}}

function T.new(app,args)
    return setmetatable({app=app,args=args,initFrames=0},T)
end
function T:initialize()
    local originalArgs=self.args
    if originalArgs.teamOnline and not originalArgs.teamMatched then self.app:travel('online',{teamOnline=true});return end
    local full=Base.new(self.app,{mode='versus',cpu=true,previewRoster=true})
    for k,v in pairs(full) do self[k]=v end
    self.args=originalArgs
    self.mode=self.args.teamOnline and 'teamOnline' or 'teamSolo'
    self.teams={{},{}};self.edit=1;self.phase='chars';self.notice=''
    self.ready={false,false};self.focused=false;self.cpuAt=.7
    self.thumbs={{},{}};self.thumbKeys={{},{}}
    self.opponentTag=self.args.cpu==false and '2P' or 'CPU'
    self.cur={1,1}
    self.app.input:clearUI()
    self:bindAreas()
    self.initialized=true
    if self.args.teamOnline then
        if self.args.teamMatched then
            self.teamIO=self.args.teamIO or self.app.net.teamDraft
            self.app.teamSelectionIO=self.teamIO;self.netEpoch=self.teamIO.epoch
            return
        end
        self.app.teamSelectionIO=self.app.teamSelectionIO or self.app.env.teamio or require('gf_team_selection').new(self.app.env.game,self.app.env.script,function()return self.app.t end)
        self.teamIO=self.app.teamSelectionIO;self.teamIO.start();self.netEpoch=self.teamIO.epoch
    end
end
function T:activePlayer() return self.edit end
function T:bindAreas()
    self.cardAreas={}
    for i=1,#Art.roster do
        local idx=i;local x,y=self:cardPos(i)
        self.cardAreas[i]=self.app.input:area(x,y,104,128,{down=function()
            if #self.teams[1]<4 and not self.ready[1] then
                if self.cur[1]==idx and self.focused and not self:inTeam(idx) then self:confirm()
                else self.cur[1]=idx;self.focused=true;self.notice='' end
            end
        end})
    end
end
function T:inTeam(idx)
    for _,v in ipairs(self.teams[1]) do if v==idx then return true end end
    return false
end
function T:confirm()
    local team=self.teams[1];local idx=self.cur[1]
    if #team==4 then
        self.ready[1]=not self.ready[1];self.startAt=nil
        self.notice=self.ready[1] and (self.teamIO and not self.teamIO.slot and '阵容已保存 · 等待服务器席位' or '已准备 · 等待对方') or '已取消准备'
        if self.teamIO then self.teamIO.publish(team,self.ready[1]) end
        return
    end
    if not self.focused then self.focused=true;return end
    for _,v in ipairs(team) do if v==idx then self.notice='该角色已选择';return end end
    if #team>=4 then return end
    team[#team+1]=idx;self.notice='';self.app.audio:play(self.app.audio.ID.okBig)
    self.focused=false
    if self.teamIO then self.teamIO.publish(team,false) end
end
function T:action(a)
    local p=self.edit;local team=self.teams[p]
    if a=='ok' then self:confirm()
    elseif a=='back' then
        self.notice=''
        if self.ready[1] then self.ready[1]=false;self.startAt=nil
        elseif #team>0 then self.cur[p]=table.remove(team);self.focused=true
        else
            if self.args.teamMatched then self.app.net.me.selecting=false;self.app.net.me.teamMode=false end
            self.app:travel('menu')
        end
        if self.teamIO then self.teamIO.publish(team,self.ready[1]) end
    elseif a=='alt' then
        local start=math.floor(self.t*977)%#Art.roster+1
        for n=0,#Art.roster-1 do
            local idx=(start+n-1)%#Art.roster+1;local exists=false
            for _,v in ipairs(team) do if v==idx then exists=true end end
            if not exists then self.cur[p]=idx;self.focused=true;break end
        end
    elseif a=='left' or a=='right' or a=='up' or a=='down' then
        local d=(a=='left' or a=='up') and -1 or 1
        if #team<4 then self.cur[p]=(self.cur[p]-1+d)%#Art.roster+1;self.focused=true end
    end
end
function T:tick()
    if not self.initialized then
        self.initFrames=self.initFrames+1
        if self.initFrames>=2 then self:initialize() end
        return
    end
    self.t=self.t+1/60;self.frameN=(self.frameN or 0)+1
    self.loadingPose=false
    for _,a in ipairs(self.app.input:menu()) do self:action(a) end
    -- Local CPU chooses privately; only its count/ready status reaches the selection view.
    if not self.teamIO and #self.teams[2]<4 and self.t>=self.cpuAt then
        local idx=(#self.teams[2]*2+math.floor(self.cpuAt*17))%#Art.roster+1
        local used={};for _,v in ipairs(self.teams[2]) do used[v]=true end
        while used[idx] do idx=idx%#Art.roster+1 end
        self.teams[2][#self.teams[2]+1]=idx;self.cpuAt=self.t+.7
        self.ready[2]=#self.teams[2]==4
    end
    if self.teamIO then
        self.teamIO.pump()
        if self.args.teamMatched and not require('gf_online').opponent(self.app.net) then
            self.teamIO.stop();self.app:travel('online',{teamOnline=true});return
        end
        if self.teamIO.slot and not self.netSeatAssigned then
            self.netSeatAssigned=true;self.netEpoch=self.teamIO.epoch
        elseif self.netEpoch~=self.teamIO.epoch then
            self.netEpoch=self.teamIO.epoch;self.teams[1]={};self.ready[1]=false;self.startAt=nil;self.focused=false
        end
        self.ready[2]=self.teamIO.remoteReady
        if self.teamIO.error then self.notice='联机信号失败：'..self.teamIO.error
        elseif not self.teamIO.slot and self.t>3 then self.notice='阵容可先选择 · GF3席位未返回，请核对独立节点挂载与信号名' end
    end
    if self.ready[1] and self.ready[2] and (not self.teamIO or self.teamIO.reveal) then
        self.startAt=self.startAt or self.t+1
        if self.t>=self.startAt and not self.leaving then
            self.leaving=true
            local source=self.teamIO and self.teamIO.reveal or self.teams
            local copy={{},{}};for q=1,2 do for n,v in ipairs(source[q]) do copy[q][n]=v end end
            self.app:travel('gf_scene_team_vs',{teams=copy,teamOnline=self.args.teamOnline,teamMatched=self.args.teamMatched,teamIO=self.teamIO})
        end
    end
    local p=self.edit;local key=Art.roster[self.cur[p]].key
    -- Decode and build the single large preview on separate callbacks.
    if self.frameN>=4 and (self.previewKey~=key or self.previewPlayer~=p) then
        self.previewKey=key;self.previewPlayer=p
        self.previewImage=Art.pose(key,self.tier,'idle')
        self.shows[p].bmp:start(self.previewImage,key..':team-idle')
        self.shows[p].bmp.node:on(false);self.shows[3-p]:hide()
        self.loadingPose=true;return
    end
    if self.bd then self.bd:step(self.built<#Art.roster and 40 or 300) end
    if self.frameN>=2 then self:buildCards() end
    if self.built==#Art.roster then
        for q=1,1 do for n=1,4 do
            local idx=self.teams[q][n]
            if self.thumbKeys[q][n]~=idx then
                local b=self.thumbs[q][n]
                if idx then
                    if not b then b=G.bitmap(self.cardsG);self.thumbs[q][n]=b end
                    local face=Art.face(Art.roster[idx].key)
                    b:drawMany({{img=face,ox=0,oy=-22,s=44/face.h}})
                elseif b then b.node:on(false) end
                self.thumbKeys[q][n]=idx;return
            end
        end end
    end
end
function T:teamBarPos(p,n)
    local W,H=self.app.W,self.app.H
    local originalWidth=math.min(1040,W/2+60)
    local originalSlot=(originalWidth-220)/4-12
    local step=originalSlot/2+12
    local w=220+4*step
    local textWidth=math.min(760,W/2-180)
    local left=W/4-280-textWidth/2
    local x,y=left+w/2,-H/2+432+(p==1 and 72 or 0)
    if not n then return x,y,w end
    return x-w/2+220+(n-.5)*step,y+7,step-12
end
function T:drawTeamBacks(B)
    if (self.frameN or 0)<6 then return end
    for p=1,1 do
        local x,y,w=self:teamBarPos(p)
        UI.parallelogram(B,x,y,w,70,UI.NAVY,.96,UI.GOLD)
        for n=1,4 do local sx,sy,sw=self:teamBarPos(p,n)
            UI.parallelogram(B,sx,sy,sw,48,UI.NAVY2,1,UI.GOLD)
        end
    end
end
function T:drawTeamBars(L)
    if (self.frameN or 0)<7 then return end
    for p=1,1 do
        local x,y,w=self:teamBarPos(p);local left=x-w/2
        UI.parallelogram(L,left+48,y+8,64,26,colors[p],1)
        L:label(self.teamIO and (self.teamIO.slot and self.teamIO.slot..'P' or '…') or '1P',left+48,y+8,64,26,17,UI.TEXT,'c')
        L:label('阵容  '..#self.teams[p]..'/4',left+148,y+8,128,26,18,UI.GOLD,'c')
        for n=1,4 do
            local sx,sy,sw=self:teamBarPos(p,n);local idx=self.teams[p][n]
            local b=self.thumbs[p][n]
            if b then b.node:pos(sx,sy):on(idx~=nil and self.thumbKeys[p][n]==idx) end
            L:label(n==4 and '协' or tostring(n),sx-sw/2+14,sy+8,24,24,14,UI.CREAM,'c')
            if not idx then L:label('+',sx,sy,sw,32,25,UI.GOLD,'c') end
        end
        local count=self.teamIO and self.teamIO.remoteCount or #self.teams[2]
        local status=self.ready[2] and '对方已准备' or ('对方已选 '..count..'/4')
        if self.teamIO and not self.teamIO.slot then status=self.t>3 and 'GF3席位未返回 · 请检查独立节点挂载' or '正在取得服务器席位' end
        if self.teamIO and self.teamIO.error then status='GF3信号发送失败 · 请检查信号名' end
        L:label(status,left+w/2,y-65,w,30,19,UI.CREAM,'c')
        local prompt=self.ready[1] and '己方已准备 · 再点按钮可取消' or (#self.teams[1]==4 and '顺序已固定 · 核对阵容后准备' or (#self.teams[1]==3 and '第4选：协同角色' or ('选择第'..(#self.teams[1]+1)..'位')))
        L:label(prompt,left+w/2,y+61,w+100,28,18,UI.GOLD,'c')
    end
end
function T:drawNameAction(L,c,bx,y,width,a)
    local label
    if #self.teams[1]==4 then label=self.ready[1] and '取消准备' or '准备' end
    local x=bx-width/2+155
    if label then
        local enabled=label~='已选择'
        UI.parallelogram(L,x,y,310,76,enabled and UI.CREAM or UI.NAVY2,a,UI.GOLD)
        L:label(label,x,y,310,76,46,enabled and UI.TEXT or UI.GREY,'c',nil,a)
        UI.tap(L,'teamConfirm',x,y,310,76,'ok',enabled)
    else
        L:label(c.name,bx,y,width,100,78,UI.WHITE,'l',nil,a)
        UI.tap(L,'teamConfirm',x,y,310,76,'ok',false)
    end
end
function T:cardLabel(i,c)
    if #self.teams[1]<4 and self.focused and i==self.cur[1] and not self:inTeam(i) then return '确认' end
    return c.name
end
function T:previews()
    local p=self.edit;local show=self.shows[p]
    if not self.previewImage then return end
    if show.bmp.job and not show.bmp:step(200) then return end
    local x,y=-(self.app.W/2-330),-self.app.H/2+372
    show.bmp.node:pos(x,y):scale(self.previewImage.u*1.2):on(true)
    show.shadow:pos(x,y+5):size(280,40):color(0,0,0,120):on(true)
end
function T:drawMarkers(L)
    for p=1,1 do
        local markers={}
        for n,idx in ipairs(self.teams[p]) do markers[#markers+1]={idx=idx,n=n,locked=true} end
        local exists=false
        for _,v in ipairs(self.teams[p]) do if v==self.cur[p] then exists=true end end
        if p==self.edit and #self.teams[p]<4 and not exists then markers[#markers+1]={idx=self.cur[p],n=#self.teams[p]+1} end
        for _,m in ipairs(markers) do
            local x,y=self:cardPos(m.idx);local col=colors[p]
            local a=m.locked and 1 or (.75+.25*math.sin(self.t*9))
            local overlap=false
            local off=p==2 and overlap and 5 or 0
            local fw,fh=112+off*2,136+off*2
            L:rect(x,y+fh/2,fw+5,5,col,a);L:rect(x,y-fh/2,fw+5,5,col,a)
            L:rect(x-fw/2,y,5,fh,col,a);L:rect(x+fw/2,y,5,fh,col,a)
            local tx=x+(p==1 and -24 or 24)
            -- Keep the original top-of-portrait tags; stack only on shared portraits.
            local ty=y+fh/2-12-(p==2 and overlap and 28 or 0)
            local label=(self.teamIO and self.teamIO.slot and self.teamIO.slot..'P' or '1P')..'-'..m.n
            UI.slab(L,tx,ty,72,26,col,a,8)
            L:label(label,tx,ty,72,26,15,UI.TEXT,'c',nil,a)
        end
    end
end
function T:draw()
    if not self.initialized or self.loadingPose or (self.frameN or 0)<2 then return end
    Base.draw(self)
end
function T:resize() if self.initialized then Base.resize(self) end end
function T:exit()
    if self.initialized then
        if self.teamIO and not self.leaving then self.teamIO.reset();self.teamIO.stop() end
        for p=1,2 do for _,b in pairs(self.thumbs[p]) do b:free() end end
        Base.exit(self)
    end
end
return T
end

__loaders['gf_scene_team_vs'] = function()
local G=require('gf_gfx')
local UI=require('gf_ui')
local Art=require('gf_selection_art')
local S={};S.__index=S
function S.new(app,args)
    return setmetatable({app=app,teams=args.teams,args=args,epoch=args.teamIO and args.teamIO.epoch,t=0,built=0,faces={},group=G.group(app.layers.world),B=G.layer(app.layers.back),L=G.layer(app.layers.ui)},S)
end
function S:pos(p,n)
    local W=self.app.W
    local step=math.min(155,(W/2-180)/4)
    return (p==1 and -1 or 1)*W/4+(n-2.5)*step,30
end
function S:tick()
    self.t=self.t+1/60
    if self.args.teamIO then
        self.args.teamIO.pump()
        if self.args.teamMatched and not require('gf_online').opponent(self.app.net) then
            self.args.teamIO.stop();self.app:travel('online',{teamOnline=true});return
        end
        if self.args.teamIO.epoch~=self.epoch then
            self.app:travel(self.args.teamMatched and 'online' or 'select',self.args.teamMatched and {teamOnline=true} or {teamPreview=true,teamOnline=true});return
        end
    end
    if self.built<8 then
        self.built=self.built+1
        local p=(self.built-1)//4+1;local n=(self.built-1)%4+1
        local img=Art.face(Art.roster[self.teams[p][n]].key)
        local b=G.bitmap(self.group);b:drawMany({{img=img,ox=0,oy=-50,s=100/img.h}})
        self.faces[self.built]=b
    end
    for _,a in ipairs(self.app.input:menu()) do
        if a=='back' then
            if self.args.teamIO then self.args.teamIO.reset();self.args.teamIO.stop() end
            self.app:travel(self.args.teamMatched and 'online' or 'select',self.args.teamMatched and {teamOnline=true} or {teamPreview=true,teamOnline=self.args.teamOnline});return
        end
    end
    if self.built==8 and self.t>=2 then self:startBattle() end
end
function S:startBattle()
    if self.starting then return end
    local R=require('gf_roster');local teams={{},{}}
    local assists={}
    for side=1,2 do for n=1,3 do teams[side][n]=R[self.teams[side][n]] end;assists[side]=R[self.teams[side][4]] end
    local args={mode='team',teamMode=true,teamRoster=teams,assistChars={assists[1].key,assists[2].key},chars={teams[1][1].key,teams[2][1].key},cpu={false,self.app.settings.cpu},rounds=1,time=self.app.settings.time}
    if self.args.teamOnline then
        local O=require('gf_online');local net=self.args.teamMatched and self.app.net or self.app:netOn('GF3Battle',self.epoch)
        if not net.slot or net.slot~=self.args.teamIO.slot then return end
        net.me.assist=self.teams[net.slot][4];net.me.char=self.teams[net.slot][1];net.me.selecting=true;net.me.ready=true
        net.host.stage=1;net.host.rounds=1;net.host.time=self.app.settings.time
        local function options(chars,setup,seed)return {teams=teams,assistChars=assists,chars={teams[1][1],teams[2][1]},rounds=1,time=setup.time,seed=seed} end
        if O.isHost(net) then if not net.match and O.bothReady(net) then O.hostStart(net,nil,options) end
        else O.checkJoin(net,nil,options) end
        if not net.match then return end
        args.mode='online';args.online=true;args.cpu={false,false}
        args.teamMatched=self.args.teamMatched
    end
    self.starting=true
    if self.args.teamIO then self.args.teamIO.stop() end
    self.app:travel('fight',args)
end
function S:draw()
    local W,H=self.app.W,self.app.H
    local B=self.B;B:begin();self.app:cover(B,UI.NAVY,1)
    UI.slab(B,-W*.25,0,W*.52,H*1.5,{35,25,60},.8,-UI.SLANT)
    UI.slab(B,W*.25,0,W*.52,H*1.5,{20,42,61},.8,-UI.SLANT)
    for p=1,2 do for n=1,4 do local x,y=self:pos(p,n)
        UI.parallelogram(B,x,y,120,120,UI.NAVY2,1,UI.GOLD)
    end end
    B:finish()
    local L=self.L;L:begin()
    L:label('阵容揭晓',0,H/2-90,600,70,46,UI.WHITE,'c')
    L:label('VS',0,40,170,100,70,UI.GOLD,'c')
    for p=1,2 do
        L:label(p==1 and '1P' or (self.args.teamOnline and '2P' or 'CPU'),(p==1 and -1 or 1)*W/4,160,300,44,30,UI.CREAM,'c')
        for n=1,4 do
            local x,y=self:pos(p,n);local b=self.faces[(p-1)*4+n]
            if b then b.node:pos(x,y) end
            -- Portraits sit above their background, while labels sit below them.
            local c=Art.roster[self.teams[p][n]]
            L:label(c.name,x,y-90,145,30,19,UI.WHITE,'c')
            L:label(n==4 and '协同' or tostring(n),x,y-120,130,26,16,UI.GOLD,'c')
        end
    end
    UI.prompt(L,-90,-H/2+70,'K','返回选人',1,'back')
    L:finish()
end
function S:exit()
    for _,b in ipairs(self.faces) do b:free() end
    G.release(self.group);self.B:free();self.L:free()
end
return S
end
