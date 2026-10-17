__loaders['gf_app_loading']=function()
local G=require('gf_gfx')
return function(App)
function App:advanceInitialAssets(dt)
    local state=self.initialAssets
    self:fit(false)
    state.elapsed=state.elapsed+math.max(0,dt or 0)
    if state.i>#state.keys then
        self.assetPreparationSeconds=state.elapsed
        self.initialAssets=nil
        return false
    end
    if not state.job then
        state.job=require('gf_art').prepare(state.keys[state.i],'lo')
        state.total=state.total+(state.job.total or 0)
    elseif state.job:step(9000) then
        state.completed=state.completed+(state.job.total or 0)
        state.job=nil;state.i=state.i+1
    end
    self.poolLoadingL=self.poolLoadingL or G.layer(self.view)
    local L=self.poolLoadingL;L.node:front();L:begin()
    self:cover(L,{0,0,0},1)
    L:label('素材准备 · '..(GF_ASSET_PROFILE or '对照'),0,48,640,44,28,{236,229,216})
    L:label(('角色 %d/%d · %.1f 秒'):format(math.min(state.i,#state.keys),#state.keys,state.elapsed),0,-8,640,36,22,{211,188,142})
    L:label(('%d 帧完成'):format(state.completed+(state.job and state.job.completed or 0)),0,-48,640,32,20,{165,165,165})
    L:finish()
    return true
end

function App:drawScenePool(state)
    local pending = self.poolNext
    local total = math.max(1, state.target - pending.start)
    local progress = math.max(0, math.min(1, (state.total - pending.start) / total))
    self.poolLoadingL = self.poolLoadingL or G.layer(self.view)
    local L = self.poolLoadingL
    L.node:front()
    local width = math.min(560, self.W - 160)
    L:begin()
    self:cover(L,{0,0,0},1)
    L:label('正在加载', 0, 48, width, 44, 28, {236, 229, 216})
    L:rect(0, 0, width, 6, {45, 45, 45}, 1)
    L:rect((progress - 1) * width / 2, 0, width * progress, 6, {211, 188, 142}, 1)
    L:label(('%d%%'):format(math.floor(progress * 100)), 0, -36, width, 32, 20, {165, 165, 165})
    L:finish()
    self.env.host:SetVisible(false)
end

function App:requestScenePool(name, args)
    local battlePool=self:isMobile() and (GF_MOBILE_BATTLE_IMAGE_POOL or 12000) or (GF_BATTLE_IMAGE_POOL or 16000)
    -- Spread the extra 2000 over selection, VS and battle, never one burst.
    local extra=math.max(0,battlePool-14000)
    local tranche=math.ceil(extra/3/32)*32
    local needs = {intro=1800, title=8000, menu=3200, options=3200, howto=6400,
                   select=math.min(battlePool,14000+tranche), online=12000,
                   vs=math.min(battlePool,14000+tranche*2),fight=battlePool,result=6400,test=256}
    if self:isMobile() then needs.select=7000;needs.online=7000;needs.vs=9000;needs.gf_scene_team_vs=7000 end
    local start = G.secondPoolStatus().total
    local ready=G.requestImages(needs[name] or 9500)
    if ready and G.retiredPending()==0 and #G.trash==0 then return false end
    self.poolNext = {name=name, args=args, start=start}
    self:drawScenePool(G.secondPoolStatus())
    return true
end
function App:advanceScenePool()
    local pending = self.poolNext
    if not pending then return false end
    if G.retiredPending()>0 or #G.trash>0 then
        self:drawScenePool(G.secondPoolStatus())
        return true
    end
    local done = G.growImages()
    self:drawScenePool(G.secondPoolStatus())
    if done then
        self.poolNext = nil
        self.poolLoadingL:free()
        self.poolLoadingL = nil
        self:go(pending.name, pending.args)
    end
    return true
end


end
end
