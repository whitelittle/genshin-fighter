__loaders['gf_app_network']=function()
local G=require('gf_gfx')
return function(App)
function App:netOn(family,epoch)
    family=family or 'GFV2'
    if self.net and family=='GF3Battle' and epoch and self.net.io.epoch~=epoch then
        if self.net.io.stop then self.net.io.stop() end;self.net=nil
    end
    if self.net and (self.netFamily or 'GFV2')~=family then
        if self.net.io.stop then self.net.io.stop() end;self.net=nil
    end
    if not self.net then
        local io=family=='GFV2' and self.env.netio or self.env.teamBattleIO
        if not io then io=require('gf_transport').new(self.env.game,self.env.script,function()return self.t end,{family=family,epoch=epoch}) end
        if io.start then io.start() end
        if family=='GF3Battle' then io.epoch=epoch end
        self.net=require('gf_online').new(io);self.netFamily=family
    end
    return self.net
end

function App:netPump()
    local o = self.net
    if not o then return end
    local O = require('gf_online')
    if o.io.pump then o.io.pump() end
    O.poll(o)
    local sc = self.scene
    if sc and sc.online and sc.state == 'run' and o.match then return end
    O.keepAlive(o)
end


end
end
