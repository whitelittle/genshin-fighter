__loaders['gf_app_metrics']=function()
local G=require('gf_gfx')
local UI=require('gf_ui')
return function(App)
-- OnUpdate frequency, not a GPU/present counter. Use raw dt before clamping.
function App:sampleFrameRate(dt)
    if type(dt)~='number' or dt<=0 then return end
    local p=self.frameRate or {elapsed=0,count=0,peak=0}
    self.frameRate=p
    p.elapsed=p.elapsed+dt;p.count=p.count+1;p.peak=math.max(p.peak,dt)
    if p.elapsed>=1 then
        p.fps=p.count/p.elapsed;p.maxMs=p.peak*1000
        p.elapsed=0;p.count=0;p.peak=0
    end
end

function App:drawFrameRate()
    local visible=GF_FPS_VISIBLE~=false and self.sceneName=='fight'
    if not visible then
        if self.fpsLayer then self.fpsLayer.node:on(false) end
        return
    end
    if not self.fpsLayer then self.fpsLayer=G.layer(self.layers.debug) end
    local L,p=self.fpsLayer,self.frameRate or {}
    L.node:on(true);L:begin()
    -- Under the left health bar, away from timer and mobile controls.
    local x,y=-self.W/2+325,self.H/2-208
    local height=self.assetPreparationSeconds and 72 or 52
    UI.slate(L,x,y,320,height,.85)
    local text=p.fps and ('FPS %.1f | max %.0f ms\n丢时 %.0f ms'):format(p.fps,p.maxMs,(self.droppedTime or 0)*1000) or 'FPS 采样中'
    if self.assetPreparationSeconds then text=text..('\n素材准备 %.1f s'):format(self.assetPreparationSeconds) end
    L:label(text,x,y,306,height-4,17,UI.WHITE,'l')
    L:finish()
end

function App:samplePerformance(dt)
    if GF_PERF_ENABLED==false and not self.debug then return end
    local n=G.N
    -- bitmap writes are a subset of N.pos: do not count them twice.
    local writes=(n.pos or 0)+(n.size or 0)+(n.col or 0)+(n.vis or 0)+(n.par or 0)+(n.txt or 0)
    local s=G.secondPoolStatus()
    local m=self.net and self.net.match
    local net=m and m.session
    local p=self.perf or {samples=0,sum=0,max=0,slow=0,lastWrites=0,lastBitmap=0,lastCreated=0,lastDecode=0,writes=0,windowT=0}
    local bitmap=n.bitmap or 0
    local decoded=require('gf_util').decodedBytes or 0
    p.samples=p.samples+1;p.sum=p.sum+dt;p.windowT=p.windowT+dt
    p.max=math.max(p.max,dt);if dt>1/30 then p.slow=p.slow+1 end
    p.frameWrites=math.max(0,writes-p.lastWrites);p.lastWrites=writes;p.writes=p.writes+p.frameWrites
    p.frameBitmapWrites=math.max(0,bitmap-p.lastBitmap);p.lastBitmap=bitmap
    p.frameCreated=math.max(0,s.created-p.lastCreated);p.lastCreated=s.created
    p.frameDecoded=math.max(0,decoded-p.lastDecode);p.lastDecode=decoded
    p.maxFrameWrites=math.max(p.maxFrameWrites or 0,p.frameWrites)
    p.maxBitmapWrites=math.max(p.maxBitmapWrites or 0,p.frameBitmapWrites)
    p.created=(p.created or 0)+p.frameCreated;p.decoded=(p.decoded or 0)+p.frameDecoded
    p.waits=m and (m.waits or 0) or 0
    p.syncWaits=m and (m.syncWaits or 0) or 0
    p.stalls=net and net.stats.stalls or 0
    p.predict=net and math.max(0,net.frame-net.confirmed) or 0
    p.maxPredict=net and net.maxPredict or 0
    p.rollbacks=net and net.stats.rollbacks or 0
    p.droppedMs=(self.droppedTime or 0)*1000
    p.simTick=self.scene and self.scene.sim and self.scene.sim.tick or 0
    self.perf=p
    if p.windowT>=2 then
        print(('GF_PERF scene=%s dt_avg_ms=%.1f dt_max_ms=%.1f slow=%d ui_calls=%d ui_peak=%d bitmap_peak=%d created=%d decoded=%d waits=%d sync_waits=%d stalls=%d predict=%d/%d rollback=%d dropped_ms=%.1f sim_tick=%d'):format(
            tostring(self.sceneName),p.sum/p.samples*1000,p.max*1000,p.slow,p.writes,p.maxFrameWrites,p.maxBitmapWrites,p.created,p.decoded,
            p.waits,p.syncWaits,p.stalls,p.predict,p.maxPredict,p.rollbacks,p.droppedMs,p.simTick))
        p.samples=0;p.sum=0;p.max=0;p.slow=0;p.writes=0;p.windowT=0
        p.maxFrameWrites=0;p.maxBitmapWrites=0;p.created=0;p.decoded=0
    end
end

function App:drawDebug()
    if not self.debugLayer then self.debugLayer = G.layer(self.layers.debug) end
    local L = self.debugLayer
    L:begin()
    local c = G.counts
    local s = ('FPS %d  | 场景 %s | 图片 %d/%d 文字 %d/%d | 写入 %d'):format(
        math.floor(self.fps + 0.5), tostring(self.sceneName), c.img - #G.freeImg - #(G.freeSecond or {}), c.img, c.txt - #G.freeTxt, c.txt,
        G.N.pos + G.N.size + G.N.col + G.N.vis)
    L:rect(-self.W / 2 + 330, self.H / 2 - 18, 660, 30, {0, 0, 0, 170})
    L:label(s, -self.W / 2 + 330, self.H / 2 - 18, 650, 30, 16, {120, 255, 160}, 'l')
    L:finish()
end


end
end
