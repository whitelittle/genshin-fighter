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
    job.i, job.k = i, k
    return i > n
end

function U.decodeAll(s)
    local job = U.decoder(s)
    job:step(#s + 4)
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
-- entry: gf_main
local POOLS = {img = 256, txt = 96, btn = 24}
GF_POOLS = POOLS

local root, host
local started, failed = false, false
local boot = {stage = 'collect', i = 1}
local imgs, txts, btns = {}, {}, {}
local G, App, app
local errors = 0
local stageName = 'load'

local function safe(f, ...)
    local ok, a, b = pcall(f, ...)
    if not ok then
        errors = errors + 1
        if errors <= 30 then printerr('GF error', tostring(a)) end
        return nil
    end
    return a, b
end

local function showError(message)
    failed = true
    message = '[' .. stageName .. '] ' .. tostring(message)
    printerr('GF fatal ' .. message)
    local t = host
    if not t then return end
    pcall(function()
        t:SetVisible(true)
        t:SetActive(true)
        t:SetAnchorMin(0.5, 0.5); t:SetAnchorMax(0.5, 0.5); t:SetPivot(0.5, 0.5)
        t:SetSizeDelta(1400, 320); t:SetAnchoredPosition(0, 0)
        t.fontSize = 22; t.fontColor = Color(255, 255, 255, 255); t.bgColor = Color(150, 20, 30, 235)
        t.text = '原神格斗 出错了（请截图反馈）\n' .. message
        t:SetAsLastSibling()
    end)
end

local SIGNAL = 'SQ_REC_STRIKE_V1'
local netDirty = {}
local clock = 0
local NETIO = {
    dirty = netDirty,
    player = function(name)
        local ok, v = pcall(game.GetGlobalCustomVariableValue, Enum.CustomVariableEntityType.PlayerSelf, name)
        if ok then return v end
    end,
    level = function(name)
        local ok, v = pcall(game.GetGlobalCustomVariableValue, Enum.CustomVariableEntityType.Level, name)
        if ok then return v end
    end,
    send = function(list)
        safe(function()
            local s = game.ServerSignal(SIGNAL)
            s:AddIntList(list)
            s:SendSignal()
        end)
    end,
    now = function() return clock end,
}

local function start()
    if started then return end
    host = script.object
    if not host then printerr('GF no host') return end
    started = true
    root = host.parent or host
    for k = 1, 8 do
        pcall(script.RegisterCustomVariableChangedHandler, script, Enum.CustomVariableEntityType.Level, 'GF_IN_' .. k,
              function() netDirty[k] = true end)
    end
    local ok, err = pcall(script.EnableUpdate, script, true)
    if not ok then showError('无法启用逐帧更新：' .. tostring(err)); return end
    pcall(function() host.text = 'GF LUA 已初始化 / 等待逐帧更新' end)
end

function OnInit() start() end
function OnEnable() start() end
function OnStart() start() end

function GF_APP() return app end

local function collect()
    local kids = root:GetChildren()
    boot.kids = kids
    boot.i = 1
    boot.stage = 'names'
end

local function names(budget)
    local kids = boot.kids
    local stop = math.min(#kids, boot.i + budget - 1)
    for k = boot.i, stop do
        local c = kids[k]
        local name = c.name
        if type(name) == 'string' then
            local n = tonumber(name:match('^GF_IMG_(%d+)$'))
            if n then imgs[n] = c
            else
                n = tonumber(name:match('^GF_TXT_(%d+)$'))
                if n then txts[n] = c
                else
                    n = tonumber(name:match('^GF_BTN_(%d+)$'))
                    if n then btns[n] = c end
                end
            end
        end
    end
    boot.i = stop + 1
    return stop >= #kids
end

local function dense(t)
    local out = {}
    local i = 1
    while t[i] do out[i] = t[i]; i = i + 1 end
    return out
end

local BOOT_STEPS = {
    collect = function() collect() end,
    names = function()
        if names(3000) then boot.stage = 'pools' end
    end,
    pools = function()
        G = require('gf_gfx')
        imgs, txts, btns = dense(imgs), dense(txts), dense(btns)
        if #imgs < 256 or #txts < 96 then
            error(('控件池缺失：图片 %d / %d，文字 %d / %d（检查 GIA 是否完整导入）'):format(#imgs, POOLS.img, #txts, POOLS.txt))
        end
        G.init({game = game, Enum = Enum, Color = Color, safe = safe},
               {root = root, imgs = imgs, txts = txts, btns = btns})
        local okIndex, templateIndex = pcall(script.GetParam,script,'GF_IMAGE_TEMPLATE_INDEX')
        templateIndex = okIndex and tonumber(templateIndex) or nil
        G.configureSecondPool(templateIndex or GF_DYNAMIC_IMAGE_TEMPLATE_INDEX or 1078305000)
        safe(host.SetVisible, host, false)
        pcall(function() root.disableKeyEventPassthrough = true end)
        G.parkAll()
        boot.stage = 'park'
    end,
    park = function()
        if G.flush(1800) <= 0 then boot.stage = 'app' end
    end,
    app = function()
        App = require('gf_app')
        app = App.new({game = game, Enum = Enum, Color = Color, safe = safe, host = host, root = root,
                       script = script, pools = POOLS, firstScene = GF_FIRST_SCENE, firstArgs = GF_FIRST_ARGS, settings = GF_SETTINGS,
                       netio = GF_NETIO or NETIO})
        boot.stage = 'run'
    end,
}

local diagT, diagMarker = 0, nil
local function drawVisibilityDiagnostic()
    if not host or not root then return end
    if app and G and not diagMarker then
        diagMarker = G.image(G.root, G.RECT)
        diagMarker:size(180, 24):color(255, 70, 70, 255):pos(-240, 0):on(true)
    end
    host:SetVisible(true)
    host:SetActive(true)
    host:SetAnchorMin(0.5, 0.5); host:SetAnchorMax(0.5, 0.5); host:SetPivot(0.5, 0.5)
    host:SetLocalScale(1, 1, 1)
    host:SetSizeDelta(850, 90); host:SetAnchoredPosition(0, 180)
    host.fontSize = 20
    host.fontColor = Color(255, 255, 255, 255)
    host.bgColor = Color(20, 40, 65, 245)
    local pool = G and G.secondPoolStatus()
    local view = app and app.view and app.view.c
    host.text = 'GF UI VISIBILITY PROBE / ' .. (app and app.sceneName or boot.stage or 'boot')
        .. '\nroot active=' .. tostring(root.activeInHierarchy) .. ' visible=' .. tostring(root.visible)
        .. ' / view=' .. tostring(view and view.activeInHierarchy) .. ',' .. tostring(view and view.visible)
        .. ' / images=' .. tostring(pool and pool.total or 0)
    host:SetAsLastSibling()
end

function OnUpdate(dt)
    if failed or not started then return end
    clock = clock + (dt or 0)
    if boot.stage ~= 'run' then
        stageName = 'boot:' .. boot.stage
        pcall(function() host.text = 'GF 启动阶段：' .. boot.stage end)
        local ok, err = pcall(BOOT_STEPS[boot.stage])
        if not ok then showError(err) else pcall(drawVisibilityDiagnostic) end
        return
    end
    stageName = 'run'
    local ok, err = pcall(app.update, app, dt)
    diagT = diagT + (dt or 0)
    if diagT >= 0.5 then diagT = 0; pcall(drawVisibilityDiagnostic) end
    if not ok then
        app.fatal = (app.fatal or 0) + 1
        printerr('GF update error ' .. tostring(err))
        if app.fatal > 20 then showError(err) end
    end
end

function GF_SECOND_POOL_STATUS() return G and G.secondPoolStatus() end
