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

local clock = 0

local function start()
    if started then return end
    host = script.object
    if not host then printerr('GF no host') return end
    started = true
    root = host.parent or host
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
        -- Actual image template resource index supplied for this editor project.
        local okIndex,templateIndex=pcall(script.GetParam,script,'GF_IMAGE_TEMPLATE_INDEX')
        templateIndex=okIndex and tonumber(templateIndex) or nil
        G.configureSecondPool(templateIndex or GF_DYNAMIC_IMAGE_TEMPLATE_INDEX or 1073742224)
        -- Imported fixed-size containers must follow the actual canvas on wide phones.
        safe(function()
            root:SetAnchorMin(0, 0); root:SetAnchorMax(1, 1)
            root:SetPivot(0.5, 0.5); root:SetSizeDelta(0, 0)
            root:SetAnchoredPosition(0, 0)
        end)
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
                       netio = GF_NETIO or require('gf_transport').new(game, script, function() return clock end)})
        boot.stage = 'run'
    end,
}

function OnUpdate(dt)
    if failed or not started then return end
    clock = clock + (dt or 0)
    if boot.stage ~= 'run' then
        stageName = 'boot:' .. boot.stage
        pcall(function() host.text = 'GF 启动阶段：' .. boot.stage end)
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

function GF_SECOND_POOL_STATUS() return G and G.secondPoolStatus() end


function GF_PERF_STATUS() return app and app.perf end
