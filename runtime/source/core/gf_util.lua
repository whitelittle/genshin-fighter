__loaders['gf_util'] = function()
local U = {}

local floor, sqrt, sin, cos, pi = math.floor, math.sqrt, math.sin, math.cos, math.pi
U.floor = floor

function U.clamp(v, a, b) if v < a then return a elseif v > b then return b end return v end
function U.lerp(a, b, t) return a + (b - a) * t end
function U.round(v) return floor(v + 0.5) end
function U.sign(v) if v > 0 then return 1 elseif v < 0 then return -1 end return 0 end
function U.approach(v, target, step)
    if v < target then return math.min(v + step, target) end
    return math.max(v - step, target)
end

U.ease = {
    linear = function(t) return t end,
    inQuad = function(t) return t * t end,
    outQuad = function(t) return t * (2 - t) end,
    inOutQuad = function(t) if t < 0.5 then return 2 * t * t end return -1 + (4 - 2 * t) * t end,
    outCubic = function(t) t = t - 1 return t * t * t + 1 end,
    inCubic = function(t) return t * t * t end,
    inOutCubic = function(t) if t < 0.5 then return 4 * t * t * t end t = 2 * t - 2 return 0.5 * t * t * t + 1 end,
    outBack = function(t) local s = 1.70158 t = t - 1 return t * t * ((s + 1) * t + s) + 1 end,
    outExpo = function(t) if t >= 1 then return 1 end return 1 - 2 ^ (-10 * t) end,
    outElastic = function(t)
        if t <= 0 then return 0 elseif t >= 1 then return 1 end
        return 2 ^ (-10 * t) * sin((t * 10 - 0.75) * (2 * pi / 3)) + 1
    end,
    outSine = function(t) return sin(t * pi / 2) end,
    inOutSine = function(t) return -(cos(pi * t) - 1) / 2 end,
}

function U.hex(s)
    local r, g, b, a = s:match('#?(%x%x)(%x%x)(%x%x)(%x?%x?)')
    return {tonumber(r, 16), tonumber(g, 16), tonumber(b, 16), a ~= '' and tonumber(a, 16) or 255}
end

function U.mix(c1, c2, t)
    return {c1[1] + (c2[1] - c1[1]) * t, c1[2] + (c2[2] - c1[2]) * t, c1[3] + (c2[3] - c1[3]) * t,
            (c1[4] or 255) + ((c2[4] or 255) - (c1[4] or 255)) * t}
end

function U.hash(n)
    n = (n * 1103515245 + 12345) & 0x7fffffff
    n = (n ~ (n >> 13)) * 1274126177 & 0x7fffffff
    return (n & 0xffff) / 65535
end


local B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
local DEC = {}
for i = 1, 64 do DEC[B64:byte(i)] = i - 1 end
U.B64DEC = DEC

function U.decoder(s)
    return {s = s, i = 1, n = #s, bytes = {}, k = 0, step = U.decodeStep}
end

function U.decodeStep(job, budget)
    local s, i, n, out, k = job.s, job.i, job.n, job.bytes, job.k
    local stop = math.min(n, i + budget - 1)
    stop = stop - ((stop - i + 1) % 4)
    if stop < i and i <= n then stop = math.min(n, i + 3) end
    local byte = string.byte
    while i + 3 <= stop do
        local a, b, c, d = byte(s, i, i + 3)
        local v = (DEC[a] << 18) | (DEC[b] << 12) | (DEC[c] << 6) | DEC[d]
        out[k + 1] = (v >> 16) & 255
        out[k + 2] = (v >> 8) & 255
        out[k + 3] = v & 255
        k = k + 3
        i = i + 4
    end
    U.decodedBytes=(U.decodedBytes or 0)+k-job.k
    job.i, job.k = i, k
    return i > n
end

function U.decodeAll(s)
    local job = U.decoder(s)
    job:step(#s + 4)
    return job.bytes
end

-- Compact export stores exact rectangle fields as uint8 when every field fits.
-- Ordinary exports retain uint16. Return the same unscaled five-field sequence.
function U.rectangleValues(img,raw)
    local count=img.n*5
    if img.codec=='raw' then assert(#raw==count,'invalid raw rectangle table');return raw end
    local width=img.codec=='r8' and 1 or 2
    assert(#raw>=count*width and #raw<=count*width+2,'invalid rectangle payload')
    for i=count*width+1,#raw do assert(raw[i]==0,'invalid rectangle padding') end
    if width==1 then
        if img.layout=='planes' then
            local values={}
            for i=1,img.n do
                local k=(i-1)*5
                for axis=1,5 do values[k+axis]=raw[(axis-1)*img.n+i] end
            end
            return values
        end
        for i=#raw,count+1,-1 do raw[i]=nil end
        return raw
    end
    local values={}
    for i=1,count do values[i]=raw[i*2-1]+raw[i*2]*256 end
    return values
end

U.compressionStats={blocks=0,outputBytes=0}
function U.imageDecoder(img)
    if img.compression~='lz4' then return U.decoder(img.d) end
    local fields=img.n*5*(img.codec=='r8' and 1 or 2)
    U.compressionStats.blocks=U.compressionStats.blocks+1
    local job={base=U.decoder(img.d),limit=math.ceil(fields/3)*3,inputSize=img.zlen,bytes={},phase='base64'}
    function job:step(budget)
        budget=math.max(4,budget or 9000)
        if self.phase=='done' then return true end
        if self.phase=='base64' then
            local before=self.base.i
            if not self.base:step(budget) then return false end
            budget=budget-(self.base.i-before)
            self.input=self.base.bytes;self.base=nil;self.i=1
            assert(type(self.inputSize)=='number' and self.inputSize>0 and #self.input>=self.inputSize and #self.input<=self.inputSize+2,'invalid LZ4 input size')
            for k=self.inputSize+1,#self.input do assert(self.input[k]==0,'invalid LZ4 input padding') end
            self.phase='token'
            if budget<=0 then return false end
        end
        local src,out=self.input,self.bytes
        local function read()
            assert(self.i<=self.inputSize,'truncated LZ4 block')
            local v=src[self.i];self.i=self.i+1;return v
        end
        while budget>0 do
            if self.phase=='token' then
                local token=read();self.match=token&15;self.left=token>>4
                self.phase=self.left==15 and 'literalLength' or 'literal';budget=budget-1
            elseif self.phase=='literalLength' or self.phase=='matchLength' then
                local v=read();self.left=self.left+v;budget=budget-1
                assert(self.left<=self.limit,'LZ4 length exceeds rectangle payload')
                if v~=255 then self.phase=self.phase=='literalLength' and 'literal' or 'match' end
            elseif self.phase=='literal' then
                local n=math.min(self.left,budget);local k=#out
                assert(self.i+n-1<=self.inputSize and k+n<=self.limit,'LZ4 literal overflow')
                for j=1,n do out[k+j]=src[self.i+j-1] end
                self.i=self.i+n;self.left=self.left-n;budget=budget-n
                if self.left==0 then
                    if self.i>self.inputSize then
                        assert(#out==self.limit,'LZ4 output size mismatch')
                        self.input=nil;self.phase='done'
                        U.compressionStats.outputBytes=U.compressionStats.outputBytes+#out
                        return true
                    end
                    self.phase='offset'
                end
            elseif self.phase=='offset' then
                local lo=read();self.offset=lo+read()*256
                assert(self.offset>0 and self.offset<=#out,'invalid LZ4 offset')
                self.left=self.match+4;self.phase=self.match==15 and 'matchLength' or 'match';budget=budget-2
            elseif self.phase=='match' then
                local n=math.min(self.left,budget);local k=#out
                assert(k+n<=self.limit,'LZ4 match overflow')
                for j=1,n do out[k+j]=out[k+j-self.offset] end
                self.left=self.left-n;budget=budget-n
                if self.left==0 then self.phase='token' end
            end
        end
        return false
    end
    return job
end

function U.decodeImage(img)
    if img.raw then local values=img.raw();img.raw=nil;return values end
    local job=U.imageDecoder(img)
    while not job:step(9000) do end
    return job.bytes
end

function U.palette(s)
    local b = U.decodeAll(s)
    local pal = {}
    for i = 1, #b - 2, 3 do pal[#pal + 1] = {b[i], b[i + 1], b[i + 2], 255} end
    return pal
end

return U
end

