__loaders['gf_transport'] = function()
-- V1-style seat allocation and transparent two-way string forwarding.
-- Dedicated V2 names keep the V1 three-character Team/Join protocol independent.
local T = {}
function T.new(game, script, now)
    local t = {slot=nil, nonce=nil, active=false, packets={}, dirty={}, helloAt=-99, epoch=1}
    t.diag={hello=0, seat=0, sent=0, received=0, accepted=0, rejected=0, error=nil}
    local function int(v) return tonumber(v) and math.tointeger(tonumber(v)) end
    local function emit(name, ints, payload)
        local ok,err=pcall(function()
        local s=game.ServerSignal(name)
        for _,v in ipairs(ints or {}) do s:AddInt(v) end
        if payload then s:AddString(payload); s:AddInt(t.epoch) end
        s:SendSignal()
        end)
        if not ok then t.diag.error=tostring(err);return false end
        t.diag.error=nil
        if name=='GFV2Hello' then t.diag.hello=t.diag.hello+1 else t.diag.sent=t.diag.sent+1 end
        return true
    end
    script:RegisterServerSignalHandler('GFV2Seat', function(_, p)
        t.diag.seat=t.diag.seat+1
        local slot=int(p and p[1])
        if t.active and (slot==1 or slot==2) then
            if t.slot and t.slot~=slot then t.packets={} end
            t.slot=slot
        end
    end)
    script:RegisterServerSignalHandler('GFV2FramesOut', function(_,p)
        if not t.active then return end
        t.diag.received=t.diag.received+1
        local function reject(reason) t.diag.rejected=t.diag.rejected+1;t.diag.rejectReason=reason end
        if not p then reject('参数为空');return end
        local slot, payload=int(p[1]),p[4]
        if (slot~=1 and slot~=2) or slot==t.slot or int(p[5])~=t.epoch then reject('席位或协议版本');return end
        if type(payload)~='string' or #payload>512 or payload:sub(1,5)~='GFV2:' then reject('消息格式');return end
        local packet={}
        for v in payload:sub(6):gmatch('[^,]+') do
            local n=tonumber(v)
            if not n or n%1~=0 or n < -2147483648 or n > 2147483647 then reject('整数范围');return end
            packet[#packet+1]=n
            if #packet>24 then reject('参数过多');return end
        end
        if #packet~=24 or packet[1]~=-7201 or packet[3]~=int(p[2]) then reject('长度或序号');return end
        t.diag.accepted=t.diag.accepted+1
        t.packets[slot]=packet; t.dirty[slot]=true
    end)
    function t.start()
        t.active=true; t.slot=nil; t.helloAt=-99; t.packets={};t.dirty={}
        t.diag={hello=0,seat=0,sent=0,received=0,accepted=0,rejected=0,error=nil}
        t.nonce=((math.floor(now()*1000)+1)*1103515245)&0x7fffffff
        if t.nonce==0 then t.nonce=1 end
    end
    function t.stop() t.active=false; t.packets={} end
    function t.pump()
        if t.active and now()-t.helloAt>=1 then
            t.helloAt=now(); emit('GFV2Hello')
        end
    end
    function t.player(name)
        if name=='GF_SLOT' then return t.slot end
        if name=='GF_NONCE' then return t.nonce end
    end
    function t.level(name)
        if name=='GF_SLOTS' then
            return {8,(t.slot==1 or t.packets[1]~=nil) and 1 or 0,
                      (t.slot==2 or t.packets[2]~=nil) and 1 or 0,0,0,0,0,0,0}
        end
        local k=tonumber(name:match('^GF_IN_(%d+)$'))
        return k and t.packets[k]
    end
    function t.send(packet)
        if not t.active or not t.slot then return end
        local words={}
        for i=1,24 do words[i]=tostring(packet[i]) end
        emit('GFV2Frames',{t.slot,packet[3],0},'GFV2:'..table.concat(words,','))
    end
    t.now=now
    return t
end
return T
end
