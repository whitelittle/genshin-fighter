-- 原神格斗 v2 — client entry. Mounted on the host text box GF_HOST under the client root;
-- the pooled controls GF_IMG_nnnn / GF_TXT_nnn / GF_BTN_nn are its siblings (game/native).
--
-- Lifecycle facts (client probes, genshin-ugc reference/update-7.1-20260923/CLIENT_PROBE_RESULTS.md):
-- OnInit -> OnEnable -> OnStart; sibling order cannot change before the first OnUpdate; dt is
-- in seconds. The client aborts a callback past roughly 1.2 M VM instructions and phones showed
-- only the native scene when the first frame did too much (GTA map, 2026-10-04), so the boot is
-- spread over frames and draws a visible loading bar first.
local POOLS = {img = 10000, txt = 160, btn = 24}
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

-- Online relay access for gf_online (same wiring as our 泡泡堂 map): the server graph
-- game/native/gf-relay.ts hands out GF_NONCE / GF_SLOT (PlayerSelf), writes each player's
-- packet into the Level list GF_IN_<slot> and the presence list GF_SLOTS. Packets go up as
-- a ServerSignal carrying one int list. Unverified in this map until the relay is installed.
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
    safe(script.EnableUpdate, script, true)
end

function OnInit() end
function OnEnable() start() end
function OnStart() start() end

-- offline test hooks (game/tests); unused by the game
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
        if #imgs < 1000 or #txts < 20 then
            error(('控件池缺失：图片 %d / %d，文字 %d / %d（检查 GIA 是否完整导入）'):format(#imgs, POOLS.img, #txts, POOLS.txt))
        end
        G.init({game = game, Enum = Enum, Color = Color, safe = safe},
               {root = root, imgs = imgs, txts = txts, btns = btns})
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

function OnUpdate(dt)
    if failed or not started then return end
    clock = clock + (dt or 0)
    if boot.stage ~= 'run' then
        stageName = 'boot:' .. boot.stage
        local ok, err = pcall(BOOT_STEPS[boot.stage])
        if not ok then showError(err) end
        return
    end
    stageName = 'run'
    local ok, err = pcall(app.update, app, dt)
    if not ok then
        app.fatal = (app.fatal or 0) + 1
        printerr('GF update error ' .. tostring(err))
        if app.fatal > 20 then showError(err) end
    end
end
