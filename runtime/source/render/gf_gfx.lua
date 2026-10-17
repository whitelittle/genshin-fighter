__loaders['gf_gfx'] = function()

local G = {}

G.RECT, G.ELLIPSE, G.TRI, G.STAR4, G.STAR5, G.RING = 100001, 100002, 100003, 100004, 100005, 100006

local env, safe, realSafe, Color
local N = {calls = 0, pos = 0, size = 0, col = 0, vis = 0, par = 0, txt = 0, tw = 0}
G.N = N
-- Opt-in complete bitmap jobs only. Immediate UI/particles are outside this
-- candidate budget; a layer must support hidden preparation before opting in.
function G.beginBitmapBudget(limit)
    G.bitmapBudget={limit=limit,left=limit,used=0,ownerLeft=limit}
end
function G.bitmapOwner(limit)
    if G.bitmapBudget then G.bitmapBudget.ownerLeft=limit end
end
local function takeBitmapWrites(bitmap,n)
    local b=bitmap.budgeted and G.bitmapBudget
    if not b then return true end
    if n>b.left or n>b.ownerLeft then return false end
    b.left=b.left-n;b.ownerLeft=b.ownerLeft-n;b.used=b.used+n
    return true
end
function G.endBitmapBudget()
    G.lastBitmapBudget=G.bitmapBudget;G.bitmapBudget=nil
end

local floor = math.floor
local function q(v) return floor(v * 100 + 0.5) / 100 end   -- 0.01 unit precision for the cache

local queue, qh, qt = {}, 1, 0
local direct = true     -- hot paths call the client directly unless calls are being queued
local function deferred(f, ...)
    qt = qt + 1
    queue[qt] = table.pack(f, ...)
end
function G.defer(on) safe = on and deferred or realSafe; direct = not on end
function G.flush(n)
    local stop = math.min(qt, qh + n - 1)
    for i = qh, stop do
        local t = queue[i]
        queue[i] = nil
        realSafe(table.unpack(t, 1, t.n))
    end
    qh = stop + 1
    return qt - qh + 1
end
function G.pending() return qt - qh + 1 end


local Node = {}
Node.__index = Node
G.Node = Node

local allNodes = {}
local function newNode(c, kind)
    local n=setmetatable({c = c, kind = kind}, Node)
    allNodes[#allNodes+1]=n
    return n
end

function Node:on(v)
    v = v and true or false
    if v ~= self.act then
        self.act = v
        N.vis = N.vis + 1
        if direct then self.c:SetActive(v);self.c:SetVisible(v)
        else safe(self.c.SetActive,self.c,v);safe(self.c.SetVisible,self.c,v) end
        -- Clear expired labels as well: do not rely on alpha/active alone on native mobile UI.
        if not v and self.kind=='text' then self:text('');self:outline() end
    end
    return self
end

function Node:pos(x, y)
    x, y = q(x), q(y)
    if x ~= self.x or y ~= self.y then
        self.x, self.y = x, y
        N.pos = N.pos + 1
        if direct then self.c:SetAnchoredPosition(x, y) else safe(self.c.SetAnchoredPosition, self.c, x, y) end
    end
    return self
end

function Node:size(w, h)
    if w < 0 then w = 0 end
    if h < 0 then h = 0 end
    w, h = q(w), q(h)
    if w ~= self.w or h ~= self.h then
        self.w, self.h = w, h
        N.size = N.size + 1
        if direct then self.c:SetSizeDelta(w, h) else safe(self.c.SetSizeDelta, self.c, w, h) end
    end
    return self
end

function Node:rot(r)
    r = q(r or 0)
    if r ~= self.r then
        self.r = r
        N.pos = N.pos + 1
        if direct then self.c:SetLocalRotation(0, 0, r) else safe(self.c.SetLocalRotation, self.c, 0, 0, r) end
    end
    return self
end

function Node:scale(sx, sy)
    sy = sy or sx
    sx, sy = floor(sx * 10000 + 0.5) / 10000, floor(sy * 10000 + 0.5) / 10000
    if sx ~= self.sx or sy ~= self.sy then
        self.sx, self.sy = sx, sy
        N.size = N.size + 1
        if direct then self.c:SetLocalScale(sx, sy, 1) else safe(self.c.SetLocalScale, self.c, sx, sy, 1) end
    end
    return self
end

local function c8(v)
    v = floor(v + 0.5)
    if v < 0 then return 0 elseif v > 255 then return 255 end
    return v
end

local colorCache, colorCount = {}, 0
local function colorOf(key, r, g, b, a)
    local v = colorCache[key]
    if v == nil then
        if colorCount > 6000 then colorCache, colorCount = {}, 0 end
        v = Color(r, g, b, a)
        colorCache[key] = v
        colorCount = colorCount + 1
    end
    return v
end
G.colorOf = colorOf

function Node:color(r, g, b, a)
    r, g, b, a = c8(r), c8(g), c8(b), c8(a or 255)
    local key = ((r * 256 + g) * 256 + b) * 256 + a
    if key ~= self.ck then
        self.ck = key
        N.col = N.col + 1
        local c = self.c
        local v = colorOf(key, r, g, b, a)
        if direct then
            if self.kind == 'text' then c.fontColor = v else c.imageColor = v end
        elseif self.kind == 'text' then
            safe(function() c.fontColor = v end)
        else
            safe(function() c.imageColor = v end)
        end
    end
    return self
end

function Node:rgba(t, am)
    return self:color(t[1], t[2], t[3], (t[4] or 255) * (am or 1))
end

function Node:shape(s)
    if s ~= self.sh then
        self.sh = s
        N.size = N.size + 1
        safe(self.c.SetImage, self.c, env.Enum.ImageSource.StaticReference, s)
    end
    return self
end

function Node:soft(k)
    k = k or 0
    if k == (self.sk or 0) then return self end
    local was = self.sk or 0
    self.sk = k
    N.size = N.size + 1
    local c = self.c
    safe(function()
        if k > 0 then
            if was == 0 then
                c.enableMask = true
                c.enableSoftEdge = true
                c.softEdgeMode = env.Enum.ImageMaskSoftEdgeMode.Percentage
            end
            c:SetSoftEdgeWidth(k, k)
        else
            c.enableSoftEdge = false
            c.enableMask = false
        end
    end)
    return self
end

function Node:hfill(amount, from)
    amount = floor(amount * 1000 + 0.5) / 1000
    local key = (from or 'Left') .. amount
    if key ~= self.fk then
        self.fk = key
        N.size = N.size + 1
        local c = self.c
        safe(function() c:SetFillHorizontal(env.Enum.ImageFillHorizontalType[from or 'Left'], amount) end)
    end
    return self
end

function Node:rfill(amount)
    amount = floor(amount * 1000 + 0.5) / 1000
    if amount ~= self.rf then
        self.rf = amount
        N.size = N.size + 1
        local c = self.c
        safe(function() c:SetFillRadial360(env.Enum.ImageFillRadialType.Top, amount) end)
    end
    return self
end

function Node:front()
    N.par = N.par + 1
    safe(self.c.SetAsLastSibling, self.c)
    return self
end

function Node:parentTo(p)
    if self.parent ~= p then
        self.parent = p
        N.par = N.par + 1
        local c, pc = self.c, p.c
        safe(function() c.parent = pc end)
    end
    return self:front()
end

function Node:text(s)
    s = s or ''
    if s ~= self.tv then
        self.tv = s
        N.txt = N.txt + 1
        local c = self.c
        safe(function() c.text = s end)
    end
    return self
end

function Node:font(size, align, valign)
    size = floor(size + 0.5)
    local key = size .. (align or 'c') .. (valign or 'm')
    if key ~= self.fnk then
        self.fnk = key
        N.txt = N.txt + 1
        local c = self.c
        local E = env.Enum
        safe(function()
            c.adaptiveFontSize = false
            c.minimumFontSize = 1
            c.fontSize = size
            c.horizontalAlignment = (align == 'l' and E.TextHorizontalAlignment.Left)
                or (align == 'r' and E.TextHorizontalAlignment.Right) or E.TextHorizontalAlignment.Middle
            c.verticalAlignment = (valign == 't' and E.TextVerticalAlignment.Top)
                or (valign == 'b' and E.TextVerticalAlignment.Bottom) or E.TextVerticalAlignment.Middle
        end)
    end
    return self
end

function Node:outline(r, g, b, a)
    local key = r and (((r * 256 + g) * 256 + b) * 256 + (a or 255)) or false
    if key ~= self.ok then
        self.ok = key
        N.txt = N.txt + 1
        local c = self.c
        safe(function()
            if r then c.enableOutline = true; c.outlineColor = Color(r, g, b, a or 255)
            else c.enableOutline = false end
        end)
    end
    return self
end

function Node:tween(fields, dur, ease, done)
    if self.tw then pcall(function() self.tw:Kill(false) end); self.tw = nil end
    if fields.anchoredPositionX or fields.anchoredPositionY then self.x, self.y = nil, nil end
    if fields.localScaleX or fields.localScaleY then self.sx, self.sy = nil, nil end
    if fields.localRotationZ then self.r = nil end
    if fields.sizeDeltaX or fields.sizeDeltaY then self.w, self.h = nil, nil end
    if fields.imageColor or fields.fontColor then self.ck = nil end
    if fields.fillAmount then self.fk, self.rf = nil, nil end
    N.tw = N.tw + 1
    local ok, t = pcall(env.game.Tween, self.c, fields, dur)
    if not ok or not t then if done then done() end return nil end
    if ease then pcall(function() t:SetEase(env.Enum.EaseType[ease]) end) end
    if done then pcall(function() t:SetOnComplete(done) end) end
    pcall(function() t:Play() end)
    self.tw = t
    return t
end

function Node:stop()
    if self.tw then
        pcall(function() self.tw:Kill(false) end)
        self.tw = nil
        self.x, self.y, self.sx, self.sy, self.r, self.w, self.h, self.ck = nil, nil, nil, nil, nil, nil, nil, nil
    end
    return self
end

function G.pingpong(node, a, b, dur, ease)
    local game, E = env.game, env.Enum
    node:stop()
    local ok, seq = pcall(game.TweenSequence)
    if not ok or not seq then return nil end
    local ok1, t1 = pcall(game.Tween, node.c, a, dur)
    local ok2, t2 = pcall(game.Tween, node.c, b, dur)
    if not (ok1 and ok2 and t1 and t2) then return nil end
    pcall(function()
        t1:SetEase(E.EaseType[ease or 'InOutSine'])
        t2:SetEase(E.EaseType[ease or 'InOutSine'])
        seq:Append(t1)
        seq:Append(t2)
        seq:SetLoops(-1)
        seq:Play()
    end)
    node.tw = seq
    node.x, node.y, node.ck, node.sx, node.sy, node.r = nil, nil, nil, nil, nil, nil
    return seq
end

function G.col(r, g, b, a) return Color(c8(r), c8(g), c8(b), c8(a or 255)) end


local freeImg, freeTxt, freeSecond = {}, {}, {}
G.freeImg, G.freeTxt = freeImg, freeTxt
G.counts = {img = 0, txt = 0, btn = 0, peakImg = 0, peakTxt = 0}

function G.init(e, pools)
    env = e
    realSafe = e.safe
    safe = realSafe
    Color = e.Color
    G.env = e
    G.root = newNode(pools.root, 'image')
    G.root.act = true
    for i = #pools.imgs, 1, -1 do
        local n = newNode(pools.imgs[i], 'image')
        n.pool = true
        freeImg[#freeImg + 1] = n
    end
    for i = #pools.txts, 1, -1 do
        local n = newNode(pools.txts[i], 'text')
        n.pool = true
        freeTxt[#freeTxt + 1] = n
    end
    G.btns = {}
    for i = 1, #pools.btns do G.btns[i] = newNode(pools.btns[i], 'button') end
    G.counts.img, G.counts.txt, G.counts.btn = #pools.imgs, #pools.txts, #pools.btns
end

function G.parkAll()
    local was, wasDirect = safe, direct
    safe, direct = deferred, false
    for _, n in ipairs(freeImg) do n:on(false) end
    for _, n in ipairs(freeTxt) do n:on(false) end
    for _, b in ipairs(G.btns) do b:on(false) end
    safe, direct = was, wasDirect
end

local function used()
    local ui, ut = G.counts.img - #freeImg - #freeSecond, G.counts.txt - #freeTxt
    if ui > G.counts.peakImg then G.counts.peakImg = ui end
    if ut > G.counts.peakTxt then G.counts.peakTxt = ut end
end

function G.image(parent, shape)
    local n = table.remove(freeImg) or table.remove(freeSecond)
    if not n and G.reclaimDormant then
        G.reclaimDormant()
        n=table.remove(freeImg) or table.remove(freeSecond)
    end
    if not n and G.emergencyImages and G.emergencyImages() then n=table.remove(freeSecond) end
    if not n then error('image pool exhausted; capacity='..G.counts.img, 2) end
    n.freed = nil
    n:parentTo(parent or G.root)
    n:shape(shape or G.RECT)
    n:rot(0):scale(1, 1):soft(0)
    if n.fk or n.rf then
        n.fk, n.rf = nil, nil
        local c = n.c
        safe(function() c:SetFillUnused() end)
    end
    used()
    return n
end

function G.textNode(parent)
    local n = table.remove(freeTxt)
    if not n then error('text pool exhausted', 2) end
    n.freed = nil
    n:parentTo(parent or G.root)
    n.c:SetVisible(true)
    n:rot(0):scale(1, 1)
    if not n.bgDone then
        n.bgDone = true
        local c = n.c
        safe(function() c.bgColor = Color(0, 0, 0, 0) end)
    end
    used()
    return n
end

G.trash = {}
function G.releaseLater(n)
    if n and not n.freed and not n.queued then n.queued = true; G.trash[#G.trash + 1] = n end
end

function G.flushTrash(budget)
    local t = G.trash
    local n = #t
    local stop = math.max(0, n - budget)
    for i = n, stop + 1, -1 do
        local x = t[i]
        t[i] = nil
        x.queued = nil
        G.release(x)
    end
    return #t
end

-- Fight teardown collects leaves before their parents. Drain in that order so a
-- group cannot be reused while old children still belong to it.
local retired, retireHead = {}, 1
function G.retiredPending() return #retired-retireHead+1 end
function G.flushRetired(budget)
    local stop=math.min(#retired,retireHead+budget-1)
    for i=retireHead,stop do
        local n=retired[i];retired[i]=false;n.retiring=nil
        G.release(n)
    end
    retireHead=stop+1
    if retireHead>#retired then retired={};retireHead=1 end
end
function G.release(n)
    if not n or n.freed or n.retiring then return end
    if G.deferRelease then
        n.retiring=true;retired[#retired+1]=n
        return
    end
    n:stop()
    n:on(false)
    n.freed = true
    if n.kind == 'text' then freeTxt[#freeTxt + 1] = n
    else local pool = n.secondPool and freeSecond or freeImg; pool[#pool+1] = n end
end

function G.reuse(n) n.freed = nil end

function G.group(parent)
    local n = G.image(parent, G.RECT)
    n.freed = nil
    n:size(0, 0):color(0, 0, 0, 0):pos(0, 0):on(true)
    n.kids = {}
    return n
end


local Layer = {}
Layer.__index = Layer

function G.layer(parent)
    local g = G.group(parent)
    return setmetatable({node = g, items = {}, n = 0}, Layer)
end

function Layer:begin() self.n = 0 end

function Node:sibling(i)
    N.par = N.par + 1
    if direct then self.c:SetSiblingIndex(i) else safe(self.c.SetSiblingIndex, self.c, i) end
    return self
end

local function nodeAt(L, kind)
    local i = L.n + 1
    L.n = i
    local items = L.items
    local n = items[i]
    if n and n.kind == kind then return n end
    n = nil
    for j = i + 1, #items do
        if items[j].kind == kind then n = table.remove(items, j) break end
    end
    if not n then
        if kind == 'text' then n = G.textNode(L.node) else n = G.image(L.node, G.RECT) end
        n.freed = nil
        if i > #items then items[i] = n return n end
    end
    table.insert(items, i, n)
    n:sibling(i - 1)
    return n
end

function Layer:shape(shape, x, y, w, h, col, am, rot, soft)
    local n = nodeAt(self, 'image')
    n:shape(shape):pos(x, y):size(w, h):rot(rot or 0):rgba(col, am):soft(soft or 0):scale(1):on((am or 1)>0.001)
    return n
end
function Layer:rect(x, y, w, h, col, am, rot) return self:shape(G.RECT, x, y, w, h, col, am, rot) end

function Layer:label(s, x, y, w, h, size, col, align, outline, am)
    local n = nodeAt(self, 'text')
    -- Native text can discard an entire line when its box is too short.
    -- Keep a generous line box and render large type through transform scale.
    local k = math.max(1, size / 20)
    local nativeSize = math.max(1, floor(size / k + 0.5))
    local lineHeight = math.max(h / k, nativeSize * 2)
    -- Establish geometry before assigning text and font metrics.
    n:pos(x, y):size(w / k, lineHeight):scale(k)
    n:font(nativeSize, align):rgba(col, am):text((am or 1)>0.001 and s or '')
    if outline then n:outline(outline[1], outline[2], outline[3], (outline[4] or 255) * (am or 1)) else n:outline() end
    n:on((am or 1)>0.001 and s~=nil and s~='')
    return n
end

function Layer:finish()
    local items = self.items
    for i = self.n + 1, #items do items[i]:on(false) end
end

function Layer:clear() self:begin(); self:finish() end

function Layer:free()
    for _, n in ipairs(self.items) do G.release(n) end
    self.items = {}
    G.release(self.node)
end


local dormantBitmaps=setmetatable({},{__mode='k'})
local Bitmap = {}
Bitmap.__index = Bitmap
G.Bitmap = Bitmap

local SEAM = 0.08    -- each rect grows by this many pixels so neighbours overlap (no hairlines)

function G.bitmap(parent, capacity)
    local g = G.group(parent)
    local bmp=setmetatable({node = g, kids = {}, cap = capacity or 0, used = 0, job = nil, key = nil}, Bitmap)
    dormantBitmaps[bmp]=true
    return bmp
end

function Bitmap:trim(keep)
    keep=keep or 0
    for i=#self.kids,keep+1,-1 do G.release(self.kids[i]);self.kids[i]=nil end
    self.used=math.min(self.used,keep)
    if keep==0 then self.key=nil;self.locomotionOrders=nil;self.locomotionOrderCount=nil end
end
function G.reclaimDormant()
    for bmp in pairs(dormantBitmaps) do
        if bmp~=G.activeBitmap and not bmp.pinned and not bmp.job and not bmp.node.act then bmp:trim(0) end
    end
end
function Bitmap:ensure(n)
    local previous=G.activeBitmap;G.activeBitmap=self
    local kids = self.kids
    for i = #kids + 1, n do
        local c = G.image(self.node, G.RECT)
        c.freed = nil
        kids[i] = c
    end
    G.activeBitmap=previous
end

-- Rectangles inside a contiguous palette-index run have identical RGBA and
-- shape. Their compositing commutes, including partial alpha; do not move any
-- rectangle across a run boundary. Match existing dimensions within that run
-- to avoid expensive native size writes without changing the delivered pixels.
local function locomotionOrder(img,kids)
    if img.locomotionHasRuns==false then return nil end
    local b,n=img.bytes,img.n
    local runs=1
    for i=2,n do if b[i*5]~=b[(i-1)*5] then runs=runs+1 end end
    -- Grid-ordered old assets have almost one colour run per rectangle.
    if runs>n/8 then img.locomotionHasRuns=false;return nil end
    local order,assigned={},{}
    local seam=img.seam or SEAM
    local first=1
    while first<=n do
        local last=first
        while last<n and b[(last+1)*5]==b[first*5] do last=last+1 end
        local sizes={}
        for k=first,last do
            local o=(k-1)*5
            local signature=tostring(b[o+3]+seam)..':'..tostring(b[o+4]+seam)
            local bucket=sizes[signature]
            if not bucket then bucket={};sizes[signature]=bucket end
            bucket[#bucket+1]=k
        end
        for i=first,last do
            local nd=kids[i]
            if nd then
                local bucket=sizes[tostring(nd.w)..':'..tostring(nd.h)]
                if bucket and #bucket>0 then
                    local k=table.remove(bucket)
                    -- Signature strings are only a lookup, never a geometry approximation.
                    local o=(k-1)*5
                    if nd.w==b[o+3]+seam and nd.h==b[o+4]+seam then order[i]=k;assigned[k]=true end
                end
            end
        end
        local k=first
        for i=first,last do if not order[i] then
            while assigned[k] do k=k+1 end
            order[i]=k;assigned[k]=true
        end end
        first=last+1
    end
    return order
end

function Bitmap:start(img, key, tint, reuseRuns)
    if key and key == self.key and not self.job then return true end
    -- A partly overwritten buffer no longer contains its last complete image.
    self.key = nil
    local order
    if reuseRuns then
        self.locomotionOrders=self.locomotionOrders or {}
        local cached=self.locomotionOrders[img]
        if cached==nil then
            order=locomotionOrder(img,self.kids)
            -- The permutation is always visually exact, even when dimensions
            -- later differ. Reuse it on subsequent cycles instead of allocating
            -- matching tables on every pose change. Bound this per-buffer cache.
            if (self.locomotionOrderCount or 0)>=16 then self.locomotionOrders={};self.locomotionOrderCount=0 end
            self.locomotionOrders[img]=order or false
            self.locomotionOrderCount=(self.locomotionOrderCount or 0)+1
        else order=cached or nil end
    else self.locomotionOrders=nil;self.locomotionOrderCount=nil end
    self.job = {img = img, i = 0, key = key, tint = tint,
                order=order}
    return false
end

function Bitmap:step(budget)
    local job = self.job
    if not job then return true end
    self.opacityImg,self.opacityAlpha,self.tintRGBAKey=nil,nil,nil
    local img = job.img
    local n = img.n
    local b, pal, ax, ay = img.bytes, img.pal, img.ax or 0, img.ay or 0
    local ox, oy = (img.ox or 0) - ax, (img.oy or 0) + ay
    local tint = job.tint
    local kids = self.kids
    local i = job.i
    local stop = math.min(n, i + budget)
    local writes = 0
    local processed=i
    for k = i + 1, stop do
        local o = (job.order and job.order[k] or k) * 5 - 5
        local x, y, w, h, ci = b[o + 1], b[o + 2], b[o + 3], b[o + 4], b[o + 5]
        local nd = kids[k]
        local frameBudget=self.budgeted and G.bitmapBudget
        if frameBudget and (frameBudget.left<5 or frameBudget.ownerLeft<5) then break end
        local beforeWrites=writes
        -- New leaves need all five properties; never create a whole future slice.
        if not nd then
            if not takeBitmapWrites(self,5) then break end
            self:ensure(k);nd=kids[k]
        end
        local c = nd.c
        local px, py = ox + x + w * 0.5, oy - y - h * 0.5
        local seam=img.seam or SEAM
        local sw, sh = w + seam, h + seam
        local col = tint or pal[ci + 1]
        local key = col.key
        if not key then
            key = ((col[1] * 256 + col[2]) * 256 + col[3]) * 256 + (col[4] or 255)
            col.key = key
        end
        if px ~= nd.x or py ~= nd.y then nd.x, nd.y = px, py; c:SetAnchoredPosition(px, py); writes = writes + 1 end
        if sw ~= nd.w or sh ~= nd.h then nd.w, nd.h = sw, sh; c:SetSizeDelta(sw, sh); writes = writes + 1 end
        if key ~= nd.ck then
            nd.ck = key
            c.imageColor = colorOf(key, col[1], col[2], col[3], col[4] or 255)
            writes = writes + 1
        end
        if not nd.act then
            nd.act = true
            c:SetActive(true)
            c:SetVisible(true)
            writes = writes + 2
        end
        if frameBudget then
            local cost=writes-beforeWrites
            frameBudget.left=frameBudget.left-cost;frameBudget.ownerLeft=frameBudget.ownerLeft-cost;frameBudget.used=frameBudget.used+cost
        end
        processed=k
    end
    N.pos = N.pos + writes
    N.bitmap=(N.bitmap or 0)+writes
    job.i = processed
    if processed >= n then
        if not job.keep then
            local first=job.cleanup or n+1
            for k = first, self.used do
                if kids[k].act and not takeBitmapWrites(self,2) then job.cleanup=k;return false end
                kids[k]:on(false)
            end
            self.used = n
        elseif n > self.used then
            self.used = n
        end
        self.key = job.key
        self.job = nil
        return true
    end
    return false
end

-- Tint once per palette/alpha change, then write only changed native colours.
-- Geometry and child order stay exactly as delivered.
local function setBitmapColor(nd,key,value)
 if nd.ck~=key then
  nd.ck=key;N.col=N.col+1
  if direct then nd.c.imageColor=value else safe(function()nd.c.imageColor=value end) end
 end
end
function Bitmap:opacity(img,alpha)
 alpha=alpha or 1
 if self.opacityImg==img and self.opacityAlpha==alpha then return end
 local colors={}
 for i,c in ipairs(img.pal) do
  local r,g,b,a=c8(c[1]),c8(c[2]),c8(c[3]),c8((c[4] or 255)*alpha)
  local key=((r*256+g)*256+b)*256+a
  colors[i]={key,colorOf(key,r,g,b,a)}
 end
 local needed=0
 for i=1,self.used do
  local c=colors[img.bytes[(i-1)*5+5]+1]
  if self.kids[i].ck~=c[1] then needed=needed+1 end
 end
 if not takeBitmapWrites(self,needed) then return false end
 for i=1,self.used do
  local c=colors[img.bytes[(i-1)*5+5]+1];setBitmapColor(self.kids[i],c[1],c[2])
 end
 self.opacityImg,self.opacityAlpha=img,alpha;self.tintRGBAKey=nil
end
function Bitmap:tintRGBA(r,g,b,a)
 r,g,b,a=c8(r),c8(g),c8(b),c8(a or 255)
 local key=((r*256+g)*256+b)*256+a
 if self.tintRGBAKey==key then return end
 local color=colorOf(key,r,g,b,a)
 for i=1,self.used do setBitmapColor(self.kids[i],key,color) end
 self.tintRGBAKey=key;self.opacityImg,self.opacityAlpha=nil,nil
end

function Bitmap:draw(img, key, tint)
    if self:start(img, key, tint) then return end
    self:step(img.n)
end

function Bitmap:drawMany(list)
    local total = 0
    for _, p in ipairs(list) do total = total + p.img.n end
    self:ensure(total)
    local kids = self.kids
    local k = 0
    for _, p in ipairs(list) do
        local img = p.img
        local b, pal = img.bytes, img.pal
        local s = p.s or 1
        for r = 1, img.n do
            local o = (r - 1) * 5
            local x, y, w, h, ci = b[o + 1], b[o + 2], b[o + 3], b[o + 4], b[o + 5]
            k = k + 1
            local nd = kids[k]
            nd:pos(p.ox + (x + w * 0.5 - (img.ax or 0)) * s, p.oy + ((img.ay or 0) - y - h * 0.5) * s)
            nd:size((w + (img.seam or SEAM)) * s, (h + (img.seam or SEAM)) * s)
            local c = p.tint or pal[ci + 1]
            nd:color(c[1], c[2], c[3], (c[4] or 255) * (p.alpha or 1))
            nd:on(true)
        end
    end
    for i = k + 1, self.used do kids[i]:on(false) end
    self.used = k
    self.key = nil
end

function Bitmap:hide() self.node:on(false) end
function Bitmap:show() self.node:on(true) end

function Bitmap:free()
    dormantBitmaps[self]=nil
    for _, n in ipairs(self.kids) do G.release(n) end
    self.kids = {}
    self.locomotionOrders=nil;self.locomotionOrderCount=nil
    G.release(self.node)
end

-- Experimental second pool. Only configured client templates are instantiated.
local growth = {target=0, created=0, batch=32, limit=20000, floor=GF_BATTLE_IMAGE_POOL or 16000, warning=2000, reserve=3500, destroyed=0, emergencies=0, warnings=0, retiring=false}
function G.configureSecondPool(templateIndex)
    if type(templateIndex) ~= 'number' or templateIndex <= 0 or templateIndex % 1 ~= 0 then
        error('第二池图片模板索引无效')
    end
    growth.templateIndex = templateIndex
    growth.target = G.counts.img
    growth.first = G.counts.img
end
function G.requestImages(target)
    target = math.min(growth.limit, math.max(0, target))
    growth.target = math.max(growth.target, target)
    return G.counts.img >= growth.target
end
function G.growImages(budget)
    if not growth.templateIndex then error('第二池没有配置图片模板索引') end
    if growth.failure then error(growth.failure,2) end
    local remaining = math.min(budget or growth.batch, growth.target - G.counts.img)
    for i=1,remaining do
        local ok,c = pcall(game.InstantiateClientUIControl,growth.templateIndex,G.root.c)
        if not ok or not c then
            growth.failure=('第二池创建失败：索引 %d，图片 %d/%d，已创建 %d；%s'):format(
                growth.templateIndex,G.counts.img,growth.target,growth.created,
                growth.created==0 and '请核对当前工程 B 模板的实际资源索引' or '请检查模板、控件容量与重复运行的主脚本')
            if not ok then growth.failure=growth.failure..'；'..tostring(c) end
            error(growth.failure,2)
        end
        c:SetActive(false)
        c:SetVisible(true)
        growth.created = growth.created + 1
        c.name = 'GF_DYNAMIC_IMG_' .. growth.created
        local n = newNode(c, 'image')
        n.pool, n.secondPool, n.act = true, true, false
        n.dynamicExtra=G.counts.img>=growth.floor
        freeSecond[#freeSecond+1] = n
        G.counts.img = G.counts.img + 1
    end
    return G.counts.img >= growth.target
end
function G.emergencyImages()
    if not growth.templateIndex or G.counts.img>=growth.limit then return false end
    growth.target=math.min(growth.limit,math.max(growth.target,G.counts.img+64))
    G.growImages(growth.phase=='fight' and 16 or 32);growth.emergencies=growth.emergencies+1
    return #freeSecond>0
end
function G.requestImageRetirement()
    growth.retiring=true;growth.reclaimed=false
end
function G.manageImagePool(phase, safeBoundary)
    growth.phase=phase
    if not growth.templateIndex or G.counts.img<growth.floor then return end
    local free=#freeImg+#freeSecond
    if GF_POOL_BACKGROUND_GROWTH~=false and free<growth.warning then
        growth.target=math.min(growth.limit,math.max(growth.target,G.counts.img-free+growth.reserve))
        growth.warnings=growth.warnings+1
    end
    -- Combat growth is background work. Keep the allocation-failure fallback
    -- intact; a low-free warning alone must not instantiate 64 images at once.
    if G.counts.img<growth.target then
        if GF_POOL_BACKGROUND_GROWTH~=false and phase~='fight' then G.growImages() end
    end
    -- Shrink is impossible during combat, even when all extra controls are idle.
    if not growth.retiring or phase=='fight' or not safeBoundary or G.pending()>0 or G.retiredPending()>0 or #G.trash>0 then return end
    growth.boundaryTicks=(growth.boundaryTicks or 0)+1
    if not growth.reclaimed or growth.boundaryTicks%30==0 then G.reclaimDormant();growth.reclaimed=true end
    free=#freeImg+#freeSecond
    local removable=math.min(32,G.counts.img-growth.floor,math.max(0,free-growth.reserve))
    if removable<=0 then
        if G.counts.img<=growth.floor then growth.retiring=false end
        return
    end
    local removed=0
    for i=#freeSecond,1,-1 do
        local n=freeSecond[i]
        -- Destroy only surplus leaf controls; group hierarchies are retained.
        if not n.kids and not n.tw and not n.queued and not n.retiring then
            local ok,result=pcall(game.DestroyClientUIControl,n.c)
            if ok and result~=false then
                table.remove(freeSecond,i);n.dead=true;n.c=nil
                G.counts.img=G.counts.img-1;growth.destroyed=growth.destroyed+1;removed=removed+1
            end
            if removed>=removable then break end
        end
    end
    growth.target=math.max(growth.floor,G.counts.img)
    if G.counts.img<=growth.floor then growth.retiring=false end
end
-- Fatal recovery owns no scene teardown code. Scan pooled wrappers in bounded
-- batches, returning the abandoned tree before any new scene can reuse it.
function G.beginRecovery(roots)
    G.defer(false);queue={};qh=1;qt=0
    G.deferRelease=false;G.bitmapBudget=nil;G.activeBitmap=nil
    G.trash={};retired={};retireHead=1
    for bmp in pairs(dormantBitmaps) do dormantBitmaps[bmp]=nil end
    for _,n in ipairs(roots) do if n then n:on(false) end end
    return {roots=roots,i=1,total=#allNodes}
end
function G.advanceRecovery(state,budget)
    local stop=math.min(state.total,state.i+(budget or 128)-1)
    for i=state.i,stop do
        local n=allNodes[i]
        if n and not n.dead and n.kind~='button' then
            local p=n;local owned=false
            while p do
                if p.recoveryOwner==state then owned=true;break end
                for _,r in ipairs(state.roots) do if p==r then owned=true;break end end
                if owned then break end;p=p.parent
            end
            if owned then
                n.recoveryOwner=state
                n.queued=nil;n.retiring=nil
                -- Free leaves may still be parented to an abandoned group.
                -- Detach those too before the group is reused by the title.
                n:parentTo(G.root)
                G.release(n)
            end
        end
    end
    state.i=stop+1
    return state.i>state.total
end
function G.secondPoolStatus()
    return {first=growth.first, created=growth.created, total=G.counts.img,
            target=growth.target, batch=growth.batch, templateIndex=growth.templateIndex,
            floor=growth.floor,limit=growth.limit,warning=growth.warning,reserve=growth.reserve,
            destroyed=growth.destroyed,emergencies=growth.emergencies,warnings=growth.warnings,
            retiring=growth.retiring,failure=growth.failure,freeFirst=#freeImg, freeSecond=#freeSecond,
            inUse=G.counts.img-#freeImg-#freeSecond,retired=G.retiredPending(),trash=#G.trash,
            backgroundGrowth=GF_POOL_BACKGROUND_GROWTH~=false}
end

return G
end
