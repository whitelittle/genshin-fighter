-- Offline model of the 7.1 client for the v2 game (tests and previews only).
-- Adapted from our qxsim host (genshin-ugc sim/qxsim/lua/host.lua): control tree with
-- RectTransform maths, cached fields, native-call counting, tweens, key and cursor events.
-- Members follow the community MiliLua 7.1 definitions (tests/data/api_spec.json); unknown
-- members raise so the game cannot depend on something the client does not have.
local SPEC = ...
local H = {}
local floor, max, min = math.floor, math.max, math.min

H.issues = {}
local function issue(kind, msg)
    local list = H.issues
    if #list < 200 then list[#list + 1] = kind .. ': ' .. msg end
end
H.issue = issue

---------------------------------------------------------------- Enum
local ItemMT = {__tostring = function(e) return e.FullName end}
local Enum = {}
for tname, members in pairs(SPEC.enums) do
    local t = {}
    for i = 1, #members do
        local m = members[i]
        t[m] = setmetatable({Name = m, FullName = 'Enum.' .. tname .. '.' .. m, EnumType = tname}, ItemMT)
    end
    setmetatable(t, {__index = function(_, k) error('Enum.' .. tname .. '.' .. tostring(k) .. ' is not in the 7.1 API', 2) end})
    Enum[tname] = t
end
setmetatable(Enum, {__index = function(_, k) error('Enum.' .. tostring(k) .. ' is not in the 7.1 API', 2) end})
H.Enum = Enum
local function ename(e) return type(e) == 'table' and e.Name or tostring(e) end

---------------------------------------------------------------- colours (ARGB int)
local function Color(r, g, b, a)
    local function c(v)
        if math.type(v) ~= 'integer' and v ~= floor(v) then issue('type', 'Color component not integral: ' .. tostring(v)) end
        v = floor(v)
        if v < 0 or v > 255 then issue('type', 'Color component out of range: ' .. v) end
        return max(0, min(255, v))
    end
    return (c(a or 255) << 24) | (c(r) << 16) | (c(g) << 8) | c(b)
end
H.Color = Color
local function argb(v)
    if type(v) ~= 'number' then return 255, 255, 255, 255 end
    return (v >> 16) & 255, (v >> 8) & 255, v & 255, (v >> 24) & 255
end
H.argb = argb

---------------------------------------------------------------- controls
local KIND_CLASS = {container = 'ClientUIContainerControl', image = 'ClientUIImageControl',
    text = 'ClientUITextBoxControl', button = 'ClientUIPresetButtonControl'}
local CLASS = {}
for cname, _ in pairs(SPEC.classes) do
    local fields, methods, c = {}, {}, cname
    while c do
        local d = SPEC.classes[c]
        if not d then break end
        for k, v in pairs(d.fields) do
            if type(k) == 'string' then
                if fields[k] == nil then fields[k] = v end
            else fields[v] = {access = 'ReadWrite'} end
        end
        for _, m in ipairs(d.methods) do methods[m] = true end
        c = d.base
    end
    CLASS[cname] = {fields = fields, methods = methods}
end

local DEFAULTS = {
    anchoredPositionX = 0, anchoredPositionY = 0, sizeDeltaX = 100, sizeDeltaY = 100,
    anchorMinX = 0.5, anchorMinY = 0.5, anchorMaxX = 0.5, anchorMaxY = 0.5, pivotX = 0.5, pivotY = 0.5,
    localScaleX = 1, localScaleY = 1, localScaleZ = 1, localRotationX = 0, localRotationY = 0, localRotationZ = 0,
    visible = true, active = true,
    text = '', fontSize = 20, fontColor = 0xFFFFFFFF, bgColor = 0x80000000, enableOutline = false, outlineColor = 0xFF000000,
    imageColor = 0xFFFFFFFF, fillAmount = 1, enableMask = false, enableSoftEdge = false, softEdgeWidthX = 0, softEdgeWidthY = 0,
    interactable = true, raycastTarget = true, showCursor = false, disableKeyEventPassthrough = false,
}

local nextId = 1000
H.count = 0          -- native calls since reset
H.instr = 0          -- metered VM instructions (native calls count as one)
local Control = {}
local MT = {}
H.MT = MT

local function newControl(kind, name, parent, props)
    local cname = KIND_CLASS[kind]
    nextId = nextId + 1
    local f = {}
    for k, v in pairs(DEFAULTS) do if CLASS[cname].fields[k] then f[k] = v end end
    f.name, f.id, f.alive = name, nextId, true
    if kind == 'image' then f.imageId = 100001 end
    if kind == 'text' then f.horizontalAlignment = Enum.TextHorizontalAlignment.Middle; f.verticalAlignment = Enum.TextVerticalAlignment.Middle end
    local c = setmetatable({_f = f, _cls = cname, _kind = kind, _kids = {}, _keys = {}, _cursor = {}, _parent = nil}, MT)
    if props then for k, v in pairs(props) do f[k] = v end end
    if parent then parent._kids[#parent._kids + 1] = c; rawset(c, '_parent', parent) end
    return c
end
H.newControl = newControl

MT.__index = function(c, k)
    local cls = CLASS[c._cls]
    if cls.methods[k] then
        local impl = Control[k]
        if not impl then error(c._cls .. ':' .. k .. ' is not modelled by the mock', 2) end
        return function(...)
            local n = H.instr
            H.count = H.count + 1
            local r = table.pack(impl(...))
            H.instr = n + 1
            return table.unpack(r, 1, r.n)
        end
    end
    if cls.fields[k] then
        H.count = H.count + 1
        if k == 'parent' then return c._parent end
        if k == 'activeInHierarchy' then local p = c; while p do if not p._f.active then return false end p = p._parent end return true end
        return c._f[k]
    end
    if type(k) == 'string' and k:sub(1, 1) == '_' then return nil end
    error(c._cls .. '.' .. tostring(k) .. ' is not in the 7.1 API', 2)
end
local rawNewindex
MT.__newindex = function(c, k, v)
    local n = H.instr
    rawNewindex(c, k, v)
    H.instr = n + 1
end
rawNewindex = function(c, k, v)
    if not CLASS[c._cls].fields[k] then error(c._cls .. '.' .. tostring(k) .. ' is not a field of this control', 2) end
    local spec = CLASS[c._cls].fields[k]
    if type(spec) == 'table' and spec.access and not spec.access:find('Write') then error(c._cls .. '.' .. k .. ' is read-only', 2) end
    H.count = H.count + 1
    if k == 'parent' then Control._reparent(c, v); return end
    if k == 'text' then
        if type(v) ~= 'string' then error('text expects a string', 2) end
        if #v > 1800 then issue('text', 'text of ' .. #v .. ' bytes (client cuts ~2000)') end
    end
    if k == 'fontSize' and (v < 7 or v > 120) then issue('font', 'fontSize ' .. v) end
    c._f[k] = v
end
MT.__tostring = function(c) return c._cls .. '(' .. tostring(c._f.name) .. ')' end

function Control._reparent(c, p)
    local old = c._parent
    if old then for i, k in ipairs(old._kids) do if k == c then table.remove(old._kids, i); break end end end
    rawset(c, '_parent', p)
    if p then p._kids[#p._kids + 1] = c end
end
local function num(v, what) if type(v) ~= 'number' or v ~= v then error(what .. ' expects numbers', 3) end return v end
function Control.SetAnchoredPosition(c, x, y) c._f.anchoredPositionX, c._f.anchoredPositionY = num(x, 'SetAnchoredPosition'), num(y, 'SetAnchoredPosition') end
function Control.SetSizeDelta(c, x, y) c._f.sizeDeltaX, c._f.sizeDeltaY = num(x, 'SetSizeDelta'), num(y, 'SetSizeDelta') end
function Control.SetPivot(c, x, y) c._f.pivotX, c._f.pivotY = x, y end
function Control.SetAnchorMin(c, x, y) c._f.anchorMinX, c._f.anchorMinY = x, y end
function Control.SetAnchorMax(c, x, y) c._f.anchorMaxX, c._f.anchorMaxY = x, y end
function Control.GetAnchoredPosition(c) return c._f.anchoredPositionX, c._f.anchoredPositionY end
function Control.GetSizeDelta(c) return c._f.sizeDeltaX, c._f.sizeDeltaY end
function Control.SetLocalScale(c, x, y, z) c._f.localScaleX, c._f.localScaleY, c._f.localScaleZ = num(x, 'SetLocalScale'), num(y, 'SetLocalScale'), z or 1 end
function Control.GetLocalScale(c) return c._f.localScaleX, c._f.localScaleY, c._f.localScaleZ end
function Control.SetLocalRotation(c, x, y, z) c._f.localRotationX, c._f.localRotationY, c._f.localRotationZ = x, y, num(z, 'SetLocalRotation') end
function Control.GetLocalRotation(c) return c._f.localRotationX, c._f.localRotationY, c._f.localRotationZ end
function Control.SetVisible(c, v) c._f.visible = v and true or false end
function Control.SetActive(c, v) c._f.active = v and true or false end
function Control.GetChild(c, name)
    for i = #c._kids, 1, -1 do if c._kids[i]._f.name == name then return c._kids[i] end end
end
function Control.FindChild(c, name)
    for i = #c._kids, 1, -1 do
        local k = c._kids[i]
        if k._f.name == name then return k end
        local d = Control.FindChild(k, name)
        if d then return d end
    end
end
function Control.GetChildren(c)
    local t = {}
    for i = #c._kids, 1, -1 do t[#t + 1] = c._kids[i] end
    return t
end
local function sibling(c) if c._parent then for i, k in ipairs(c._parent._kids) do if k == c then return i end end end return 1 end
local function move(c, to)
    local p = c._parent
    if not p then return end
    table.remove(p._kids, sibling(c))
    to = max(1, min(to, #p._kids + 1))
    table.insert(p._kids, to, c)
end
function Control.GetSiblingIndex(c) return sibling(c) - 1 end
function Control.SetSiblingIndex(c, i) move(c, floor(i) + 1) end
function Control.SetAsFirstSibling(c) move(c, 1) end
H.phase = 'load'
function Control.SetAsLastSibling(c)
    if H.phase ~= 'update' then issue('rule', 'SetAsLastSibling during ' .. H.phase .. ' (client refuses)'); return end
    move(c, math.huge)
end
function Control.AddKeyEventListener(c, ev, fn)
    local k = ename(ev); c._keys[k] = c._keys[k] or {}; table.insert(c._keys[k], fn)
end
function Control.RemoveAllKeyEventListeners(c) c._keys = {} end
function Control.AddCursorEventListener(c, ev, fn)
    local k = ename(ev); c._cursor[k] = c._cursor[k] or {}; table.insert(c._cursor[k], fn)
end
function Control.RemoveAllCursorEventListeners(c) c._cursor = {} end
function Control.SetImage(c, src, id)
    if type(id) ~= 'number' then error('SetImage imageId expects a number', 2) end
    c._f.imageSource, c._f.imageId = src, id
end
function Control.SetFillHorizontal(c, t, amount) c._f.fillType = 'Horizontal'; c._f.fillHorizontalType = ename(t); c._f.fillAmount = amount end
function Control.SetFillVertical(c, t, amount) c._f.fillType = 'Vertical'; c._f.fillVerticalType = ename(t); c._f.fillAmount = amount end
function Control.SetFillRadial360(c, t, amount) c._f.fillType = 'Radial360'; c._f.fillAmount = amount end
function Control.SetFillUnused(c) c._f.fillType = nil end
function Control.SetSoftEdgeWidth(c, x, y) c._f.softEdgeWidthX, c._f.softEdgeWidthY = x, y end

---------------------------------------------------------------- layout (canvas: origin bottom-left, y up)
H.W, H.H = 1600, 900
-- world transform of a control: returns a, b, c, d, e, f (x' = a x + c y + e; y' = b x + d y + f)
-- mapping local coordinates (relative to the control's pivot point) to canvas coordinates,
-- plus its rect size (w, h). Rotation/scale apply around the pivot.
local function frame(c)
    local f = c._f
    if not c._parent then
        return 1, 0, 0, 1, H.W / 2, H.H / 2, H.W, H.H
    end
    local pa, pb, pc, pd, pe, pf, pw, ph = frame(c._parent)
    local ppx, ppy = c._parent._f.pivotX or 0.5, c._parent._f.pivotY or 0.5
    -- anchor rect in parent-local coordinates (origin = parent pivot)
    local ax0, ay0 = pw * (f.anchorMinX - ppx), ph * (f.anchorMinY - ppy)
    local ax1, ay1 = pw * (f.anchorMaxX - ppx), ph * (f.anchorMaxY - ppy)
    local w, h = (ax1 - ax0) + f.sizeDeltaX, (ay1 - ay0) + f.sizeDeltaY
    local lx = ax0 + (ax1 - ax0) * f.pivotX + f.anchoredPositionX
    local ly = ay0 + (ay1 - ay0) * f.pivotY + f.anchoredPositionY
    local r = math.rad(f.localRotationZ or 0)
    local cs, sn = math.cos(r), math.sin(r)
    local sx, sy = f.localScaleX, f.localScaleY
    -- local matrix L = T(lx,ly) R S ; world = P * L
    local la, lb, lc, ld = cs * sx, sn * sx, -sn * sy, cs * sy
    local a = pa * la + pc * lb
    local b = pb * la + pd * lb
    local cc = pa * lc + pc * ld
    local d = pb * lc + pd * ld
    local e = pa * lx + pc * ly + pe
    local ff = pb * lx + pd * ly + pf
    return a, b, cc, d, e, ff, w, h
end
H.frame = frame

-- flattened draw list (paint order) for the renderer
function H.snapshot(root)
    local out = {}
    local function walk(c)
        local f = c._f
        if not (f.active and f.visible) then return end
        if c._kind == 'image' or c._kind == 'text' then
            local a, b, cc, d, e, ff, w, h = frame(c)
            local item = {c._kind, a, b, cc, d, e, ff, w, h, f.pivotX, f.pivotY}
            if c._kind == 'image' then
                local r, g, bb, al = argb(f.imageColor)
                item[12], item[13], item[14], item[15] = r, g, bb, al
                item[16] = f.imageId
                item[17] = f.enableSoftEdge and (f.softEdgeWidthX or 0) or 0
                item[18] = f.fillType or ''
                item[19] = f.fillAmount or 1
                item[20] = f.fillHorizontalType or 'Left'
            else
                local r, g, bb, al = argb(f.fontColor)
                item[12], item[13], item[14], item[15] = r, g, bb, al
                item[16] = f.text
                item[17] = f.fontSize
                item[18] = ename(f.horizontalAlignment)
                item[19] = f.enableOutline and 1 or 0
                local orr, og, ob, oa = argb(f.outlineColor)
                item[20], item[21], item[22], item[23] = orr, og, ob, oa
                local br, bg, bb2, ba = argb(f.bgColor)
                item[24], item[25], item[26], item[27] = br, bg, bb2, ba
                item[28] = ename(f.verticalAlignment)
            end
            out[#out + 1] = item
        end
        for _, k in ipairs(c._kids) do walk(k) end
    end
    walk(root)
    return out
end

-- compact text form of the draw list for the browser preview (one item per line):
-- I|a|b|c|d|e|f|w|h|px|py|r|g|b|a|shape|soft|fillType|fill|fillFrom
-- T|a|b|c|d|e|f|w|h|px|py|r|g|b|a|size|halign|valign|outline|or|og|ob|oa|br|bg|bb|ba|text
local fmt = string.format
local function n2(v) return fmt('%.2f', v) end
function H.snapshotText(root)
    local out = {}
    local function walk(c)
        local f = c._f
        if not (f.active and f.visible) then return end
        local k = c._kind
        if k == 'image' or k == 'text' then
            local a, b, cc, d, e, ff, w, h = frame(c)
            if k == 'image' then
                local r, g, bb, al = argb(f.imageColor)
                if al > 0 and w ~= 0 and h ~= 0 then
                    out[#out + 1] = table.concat({'I', fmt('%.4f', a), fmt('%.4f', b), fmt('%.4f', cc), fmt('%.4f', d), n2(e), n2(ff),
                        n2(w), n2(h), f.pivotX, f.pivotY, r, g, bb, al, f.imageId,
                        f.enableSoftEdge and n2(f.softEdgeWidthX or 0) or 0, f.fillType or '', n2(f.fillAmount or 1),
                        f.fillHorizontalType or 'Left'}, '|')
                end
            else
                local r, g, bb, al = argb(f.fontColor)
                local orr, og, ob, oa = argb(f.outlineColor)
                local br, bg, bb2, ba = argb(f.bgColor)
                local txt = (f.text or ''):gsub('\n', '\\n'):gsub('|', '/')
                if (al > 0 and txt ~= '') or ba > 0 then
                    out[#out + 1] = table.concat({'T', fmt('%.4f', a), fmt('%.4f', b), fmt('%.4f', cc), fmt('%.4f', d), n2(e), n2(ff),
                        n2(w), n2(h), f.pivotX, f.pivotY, r, g, bb, al, f.fontSize, ename(f.horizontalAlignment),
                        ename(f.verticalAlignment), f.enableOutline and 1 or 0, orr, og, ob, oa, br, bg, bb2, ba, txt}, '|')
                end
            end
        end
        for _, kid in ipairs(c._kids) do walk(kid) end
    end
    walk(root)
    return table.concat(out, '\n')
end

-- counts for perf reports
function H.stats(root)
    local s = {controls = 0, active = 0, visibleImages = 0, visibleTexts = 0, glyphs = 0}
    local function walk(c, on)
        s.controls = s.controls + 1
        on = on and c._f.active and c._f.visible
        if on then
            s.active = s.active + 1
            if c._kind == 'image' then s.visibleImages = s.visibleImages + 1 end
            if c._kind == 'text' then s.visibleTexts = s.visibleTexts + 1; s.glyphs = s.glyphs + utf8.len(c._f.text or '') end
        end
        for _, k in ipairs(c._kids) do walk(k, on) end
    end
    walk(root, true)
    return s
end

---------------------------------------------------------------- input dispatch
H.call = function(fn, ...) return fn(...) end
function H.fireKey(root, evName)
    local list = {}
    local function walk(c)
        if not c._f.active then return end
        local l = c._keys[evName]
        if l then for _, fn in ipairs(l) do list[#list + 1] = fn end end
        for _, k in ipairs(c._kids) do walk(k) end
    end
    walk(root)
    for _, fn in ipairs(list) do H.call(fn) end
    return #list
end

local EventData = {}
EventData.__index = EventData
function EventData.GetUIPos(e) return e.x, e.y end
function EventData.GetPressUIPos(e) return e.px, e.py end
function EventData.GetUIPosDelta(e) return e.dx, e.dy end

-- topmost active button containing (x, y) that listens for evName
function H.hit(root, x, y, evName)
    local best
    local function walk(c)
        local f = c._f
        if not (f.active and f.visible) then return end
        if c._kind == 'button' and f.raycastTarget ~= false and c._cursor[evName] then
            local a, b, cc, d, e, ff, w, h = frame(c)
            -- inverse of the affine (no rotation expected on buttons)
            local det = a * d - b * cc
            if det ~= 0 then
                local lx = (d * (x - e) - cc * (y - ff)) / det
                local ly = (-b * (x - e) + a * (y - ff)) / det
                local px, py = f.pivotX * w, f.pivotY * h
                if lx >= -px and lx <= w - px and ly >= -py and ly <= h - py then best = c end
            end
        end
        for _, k in ipairs(c._kids) do walk(k) end
    end
    walk(root)
    return best
end

H.touch = {}   -- touchId -> button pressed
function H.cursor(root, kind, x, y, touchId)
    touchId = touchId or -1
    local ev = ({down = 'CursorDown', up = 'CursorUp', drag = 'CursorDrag', click = 'CursorClick'})[kind]
    local target
    if kind == 'down' then
        target = H.hit(root, x, y, ev)
        H.touch[touchId] = {c = target, px = x, py = y, lx = x, ly = y}
    else
        local t = H.touch[touchId]
        target = t and t.c
    end
    local t = H.touch[touchId] or {px = x, py = y, lx = x, ly = y}
    local e = setmetatable({x = x, y = y, px = t.px, py = t.py, dx = x - t.lx, dy = y - t.ly,
                            dragging = kind == 'drag', touchId = touchId}, EventData)
    t.lx, t.ly = x, y
    if kind == 'up' then H.touch[touchId] = nil end
    if target and target._cursor[ev] then
        for _, fn in ipairs(target._cursor[ev]) do H.call(fn, e) end
        if kind == 'up' and target._cursor.CursorClick then
            for _, fn in ipairs(target._cursor.CursorClick) do H.call(fn, e) end
        end
        return true
    end
    return false
end

---------------------------------------------------------------- tweens
local EASE = {
    Linear = function(t) return t end,
    InQuad = function(t) return t * t end, OutQuad = function(t) return t * (2 - t) end,
    InOutQuad = function(t) return t < 0.5 and 2 * t * t or -1 + (4 - 2 * t) * t end,
    InCubic = function(t) return t * t * t end, OutCubic = function(t) t = t - 1; return t * t * t + 1 end,
    InOutCubic = function(t) return t < 0.5 and 4 * t * t * t or (t - 1) * (2 * t - 2) * (2 * t - 2) + 1 end,
    OutBack = function(t) local s = 1.70158; t = t - 1; return t * t * ((s + 1) * t + s) + 1 end,
    InBack = function(t) local s = 1.70158; return t * t * ((s + 1) * t - s) end,
    OutSine = function(t) return math.sin(t * math.pi / 2) end, InSine = function(t) return 1 - math.cos(t * math.pi / 2) end,
    InOutSine = function(t) return -(math.cos(math.pi * t) - 1) / 2 end,
    OutExpo = function(t) return t >= 1 and 1 or 1 - 2 ^ (-10 * t) end,
    InExpo = function(t) return t <= 0 and 0 or 2 ^ (10 * t - 10) end,
    OutQuart = function(t) return 1 - (1 - t) ^ 4 end, InQuart = function(t) return t ^ 4 end,
    OutElastic = function(t)
        if t <= 0 then return 0 elseif t >= 1 then return 1 end
        return 2 ^ (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1
    end,
    OutBounce = function(t)
        local n1, d1 = 7.5625, 2.75
        if t < 1 / d1 then return n1 * t * t elseif t < 2 / d1 then t = t - 1.5 / d1; return n1 * t * t + 0.75
        elseif t < 2.5 / d1 then t = t - 2.25 / d1; return n1 * t * t + 0.9375 end
        t = t - 2.625 / d1; return n1 * t * t + 0.984375
    end,
}
local COLOR_FIELDS = {imageColor = true, fontColor = true, bgColor = true, outlineColor = true}
local TWEENABLE = {}
for k, v in pairs(SPEC.classes.TweenTarget.fields) do TWEENABLE[type(k) == 'string' and k or v] = true end
local active = {}
H.activeTweens = active
local Tween, Seq = {}, {}
Tween.__index, Seq.__index = Tween, Seq

local function lerpColor(a, b, t)
    local ar, ag, ab, aa = argb(a)
    local br, bg, bb, ba = argb(b)
    local function L(x, y) return floor(x + (y - x) * t + 0.5) end
    return (L(aa, ba) << 24) | (L(ar, br) << 16) | (L(ag, bg) << 8) | L(ab, bb)
end

function H.Tween(obj, target, dur)
    if getmetatable(obj) ~= MT then error('game.Tween target is not a client control', 2) end
    H.count = H.count + 1
    local tw = setmetatable({obj = obj, target = {}, dur = max(dur or 0, 0), t = 0, loops = 1, ease = EASE.OutQuad,
        playing = true, relative = false}, Tween)
    for k, v in pairs(target) do
        if not TWEENABLE[k] then error('field ' .. tostring(k) .. ' is not tweenable', 2) end
        tw.target[k] = v
    end
    active[tw] = true
    return tw
end
function Tween._start(tw)
    tw.from = {}
    for k, v in pairs(tw.target) do
        tw.from[k] = tw.obj._f[k]
        if tw.relative and not COLOR_FIELDS[k] then tw.target[k] = (tw.obj._f[k] or 0) + v end
    end
end
function Tween._apply(tw, p)
    if not tw.from then tw:_start() end
    local e = tw.ease(p)
    for k, to in pairs(tw.target) do
        local from = tw.from[k]
        if COLOR_FIELDS[k] then tw.obj._f[k] = lerpColor(from, to, e)
        elseif type(from) == 'number' then tw.obj._f[k] = from + (to - from) * e
        else tw.obj._f[k] = to end
    end
end
function Tween._step(tw, dt)
    if not tw.playing then return false end
    tw.t = tw.t + dt
    local p = tw.dur > 0 and min(tw.t / tw.dur, 1) or 1
    tw:_apply(p)
    if p >= 1 then
        if tw.onStep then H.call(tw.onStep) end
        tw.loops = tw.loops - 1
        if tw.loops ~= 0 then tw.t = 0; return false end
        if tw.onComplete then H.call(tw.onComplete) end
        return true
    end
    return false
end
function Tween.Play(tw) tw.playing = true; active[tw] = true end
function Tween.Pause(tw) tw.playing = false end
function Tween.Resume(tw) tw.playing = true end
function Tween.Restart(tw) tw.t = 0; tw.from = nil; tw.playing = true; active[tw] = true end
function Tween.Complete(tw) tw:_apply(1); active[tw] = nil; if tw.onComplete then H.call(tw.onComplete) end end
function Tween.Kill(tw, complete) if complete then tw:Complete() end active[tw] = nil; tw.dead = true end
function Tween.SetEase(tw, e) tw.ease = EASE[ename(e)] or EASE.Linear end
function Tween.SetLoops(tw, n) tw.loops = n end
function Tween.SetOnComplete(tw, fn) tw.onComplete = fn end
function Tween.SetOnStepComplete(tw, fn) tw.onStep = fn end
function Tween.SetRelative(tw, r) tw.relative = r end

function H.TweenSequence()
    local s = setmetatable({items = {}, cursor = 0, t = 0, loops = 1, playing = true}, Seq)
    active[s] = true
    return s
end
local function length(tw) return tw.dur * max(tw.loops, 1) end
function Seq.Append(s, tw) active[tw] = nil; s.items[#s.items + 1] = {at = s.cursor, tw = tw}; s.last = s.cursor; s.cursor = s.cursor + length(tw) end
function Seq.Join(s, tw) active[tw] = nil; local at = s.last or 0; s.items[#s.items + 1] = {at = at, tw = tw}; s.cursor = max(s.cursor, at + length(tw)) end
function Seq.Insert(s, at, tw) active[tw] = nil; s.items[#s.items + 1] = {at = at, tw = tw}; s.cursor = max(s.cursor, at + length(tw)) end
function Seq.AppendInterval(s, d) s.cursor = s.cursor + d end
function Seq.AppendCallback(s, fn) s.items[#s.items + 1] = {at = s.cursor, fn = fn} end
function Seq.InsertCallback(s, at, fn) s.items[#s.items + 1] = {at = at, fn = fn} end
function Seq._step(s, dt)
    if not s.playing then return false end
    local t0 = s.t
    s.t = s.t + dt
    for _, it in ipairs(s.items) do
        if it.fn then
            if (it.at >= t0 and it.at < s.t) or (t0 == 0 and it.at == 0) then H.call(it.fn) end
        elseif s.t >= it.at then
            local lt = min(s.t - it.at, length(it.tw))
            local p = it.tw.dur > 0 and ((lt % it.tw.dur) / it.tw.dur) or 1
            if lt >= length(it.tw) then p = 1 end
            it.tw:_apply(p)
        end
    end
    if s.t >= s.cursor then
        if s.onStep then H.call(s.onStep) end
        s.loops = s.loops - 1
        if s.loops ~= 0 then s.t = 0; for _, it in ipairs(s.items) do if it.tw then it.tw.from = nil end end return false end
        if s.onComplete then H.call(s.onComplete) end
        return true
    end
    return false
end
Seq.Play, Seq.Pause, Seq.Resume = Tween.Play, Tween.Pause, Tween.Resume
function Seq.Restart(s) s.t = 0; s.playing = true; active[s] = true end
function Seq.Complete(s) s:_step(s.cursor - s.t + 1e-9); active[s] = nil end
function Seq.Kill(s, complete) if complete then s:Complete() end active[s] = nil end
function Seq.SetLoops(s, n) s.loops = n end
function Seq.SetOnComplete(s, fn) s.onComplete = fn end
function Seq.SetOnStepComplete(s, fn) s.onStep = fn end

function H.advanceTweens(dt)
    local list = {}
    for tw in pairs(active) do list[#list + 1] = tw end
    local n = 0
    for _, tw in ipairs(list) do
        if active[tw] then
            n = n + 1
            if tw:_step(dt) then active[tw] = nil end
        end
    end
    return n
end

---------------------------------------------------------------- signals
H.signals = {}
local Sig = {}
Sig.__index = Sig
local function addv(kind) return function(s, v) s.params[#s.params + 1] = {kind, v} end end
for _, k in ipairs({'Int', 'Float', 'Bool', 'String', 'Guid', 'Entity', 'ConfigId'}) do
    Sig['Add' .. k] = addv(k); Sig['Add' .. k .. 'List'] = addv(k .. 'List')
end
function Sig.SendSignal(s) H.signals[#H.signals + 1] = {s.name, s.params} end

---------------------------------------------------------------- game library
H.audio = {}
H.device = 'KeyboardAndMouse'
H.sticks = {left = {0, 0}, right = {0, 0}}
H.cursorPos = {800, 450}
H.vars = {}
local game = {}
H.game = game
local IMPL = {
    GetUICanvasSize = function() return H.W, H.H end,
    GetCursorUIPos = function() return H.cursorPos[1], H.cursorPos[2] end,
    PlayAudio2D = function(id) H.audio[#H.audio + 1] = id; return #H.audio end,
    StopAudio = function() end,
    IsAudioAlive = function() return false end,
    GetDevice = function() return Enum.Device[H.device] end,
    GetLanguageType = function() return Enum.LanguageType.LanguageChs end,
    GetStageMode = function() return Enum.StageMode.Beyond end,
    IsTestPlay = function() return true end,
    GetControllerLeftStickAxis = function() return H.sticks.left[1], H.sticks.left[2] end,
    GetControllerRightStickAxis = function() return H.sticks.right[1], H.sticks.right[2] end,
    GetGlobalCustomVariableValue = function(kind, name) return H.vars[ename(kind) .. ':' .. name] end,
    ServerSignal = function(name) return setmetatable({name = name, params = {}}, Sig) end,
    Tween = H.Tween,
    TweenSequence = H.TweenSequence,
    PrintClientUITree = function() end,
    GetClientUIRoots = function() return H.roots or {} end,
}
for name, _ in pairs(SPEC.game) do
    if not name:find('%.') then
        local impl = IMPL[name]
        game[name] = impl and function(...)
            local n = H.instr
            H.count = H.count + 1
            local r = table.pack(impl(...))
            H.instr = n + 1
            return table.unpack(r, 1, r.n)
        end
            or function() error('game.' .. name .. ' is not modelled by the mock', 2) end
    end
end
-- the real `game` table is a protected proxy: unknown names are nil
setmetatable(game, {__index = function() return nil end})

return H
