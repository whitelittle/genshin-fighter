-- 千星联机「输入 → 服务器 → 广播」探针 · 客户端脚本（带开局计时器 + 双向时间）
--
-- 计时器从哪来：客户端**没有**取时间的 API（模拟器 clock 未暴露，说明书里也没有函数），
--   所以用 OnUpdate(dt) 把 dt 累加 —— 这**就是游戏时钟**，比"帧数 ÷ 30"更可信
--   （不假设帧率；OnUpdate 的 dt 就是本帧时长）。
--   ⚠ 两台客户端的 t 各自从各自 OnInit 起算；模拟器里同步步进所以可比，
--     真机上必须由服务端提供公共时基（官方有没有 GetServerTime 一类 API = UNKNOWN）。
--
-- 身份：客户端不知道自己是谁 → 服务端开局按座位写 PlayerSelf.Slot，客户端读取。
-- 自/他判定：把收到的 params[1](slot) 与自己的 slot 比对 —— 相等是"我(回执)"，否则"对方"。

local TAG = "[in]"
local slot = -1
local seq = 0
local t = 0                 -- 开局计时（秒）
local shownTick = -1
local out = nil             -- 输出面板（文本视窗）
local timerBox = nil        -- 顶部计时器（文本框）
local lines = {}
local idLineIdx = nil

-- ★ 身份令牌：客户端**没有**"我是几号玩家"的 API（CustomVariableEntityType 只有
--   Level/PlayerSelf/AvatarSelf），服务端规则的**唯一取值源是 fromSignalParam**（写不出"发送者"），
--   所以浏览器里玩家自己没法知道座位号。
--   实测（runtime=simulator）：两个运行时的 tostring 地址/控件 Id 全相同，但
--   **math.random 序列天然不同** → 用随机令牌当身份，随指令发出去，收到时一比就知道是不是自己发的。
--   ⚠ 真机待验证：若各客户端同种子，令牌会撞（那就得改由服务端/关卡初始化下发身份）。
local token = math.random(1, 999999)

local WHEEL_CX, WHEEL_CY, WHEEL_R = 1230, 260, 150

local function s(v) if v == nil then return "nil" end return tostring(v) end
local function fmt(x) return string.format("%.2f", tonumber(x) or 0) end

local function refresh()
  if out == nil then return end
  local ok, err = pcall(function() out.text = table.concat(lines, "\n") end)
  if not ok then print(TAG .. " ERR 写面板失败: " .. s(err)) end
end

-- 计时器只在十分之一秒变化时刷新（每帧刷文本会白白吃绘制成本）
local function refreshTimer()
  if timerBox == nil then return end
  local tick = math.floor(t * 10)
  if tick == shownTick then return end
  shownTick = tick
  local ok, err = pcall(function() timerBox.text = "开局计时 " .. fmt(t) .. " s" end)
  if not ok then print(TAG .. " ERR 写计时器失败: " .. s(err)) end
end

local function setIdLine(text)
  if idLineIdx == nil then
    table.insert(lines, text)
    idLineIdx = #lines
  else
    lines[idLineIdx] = text
  end
  refresh()
end

local function log(line)
  table.insert(lines, line)
  refresh()
end

local function readSlot()
  local ok, v = pcall(function()
    return game.GetGlobalCustomVariableValue(Enum.CustomVariableEntityType.PlayerSelf, "Slot")
  end)
  if not ok then return -1, "pcall失败:" .. s(v) end
  if type(v) == "table" and v.value ~= nil then return tonumber(v.value) or -1, "table.value" end
  if type(v) == "number" then return v, "number" end
  return -1, "type=" .. type(v) .. " v=" .. s(v)
end

local function send(cmd)
  slot = readSlot()
  seq = seq + 1
  local sig = game.ServerSignal("Cmd")
  sig:AddInt(slot)      -- [1] 座位号（服务端写了才有；浏览器里通常是 -1）
  sig:AddInt(seq)       -- [2] 第几条
  sig:AddString(cmd)    -- [3] 什么指令
  sig:AddFloat(t)       -- [4] 发出时刻（客户端秒）
  sig:AddInt(token)     -- [5] 身份令牌
  sig:SendSignal()
  print(TAG .. " SEND slot=" .. s(slot) .. " token=" .. s(token) .. " seq=" .. s(seq) .. " cmd=" .. cmd .. " t=" .. fmt(t))
  log("我(令牌" .. s(token) .. ") 点「" .. cmd .. "」 发出 @" .. fmt(t) .. "s")
end

local function bindClick(name, cmd)
  local c = script.object:FindChild(name)
  if c == nil then
    print(TAG .. " ERR 找不到控件 " .. name)
    return
  end
  c:AddCursorEventListener(Enum.CursorEventType.CursorClick, function() send(cmd) end)
end

local bindWheel   -- 前向声明：bindPad 的回退分支要引用它
-- ★ 红白机式十字键：四个**独立**命中区，各自直接对应一个方向（不再靠角度反算）
local function bindDir(name, dir)
  local c = script.object:FindChild(name)
  if c == nil then return false end
  c:AddCursorEventListener(Enum.CursorEventType.CursorClick, function()
    print(TAG .. " PAD " .. name .. " → " .. dir)
    send(dir)
  end)
  return true
end

local function bindPad()
  local ok = bindDir("十字上", "上")
  ok = bindDir("十字下", "下") and ok
  ok = bindDir("十字左", "左") and ok
  ok = bindDir("十字右", "右") and ok
  if not ok then
    print(TAG .. " ERR 十字键命中区不全 → 回退到轮盘角度法")
    bindWheel()
  end
end

-- 旧轮盘（角度反算）保留作回退
function bindWheel()
  local w = script.object:FindChild("轮盘区")
  if w == nil then
    print(TAG .. " ERR 找不到控件 轮盘区")
    return
  end
  w:AddCursorEventListener(Enum.CursorEventType.CursorClick, function(data)
    local x, y = 0, 0
    local ok, gx, gy = pcall(function() return data:GetUIPos() end)
    if ok then x, y = gx or 0, gy or 0 end
    local dx, dy = x - WHEEL_CX, y - WHEEL_CY
    local dir
    if math.abs(dx) > math.abs(dy) then dir = dx > 0 and "右" or "左" else dir = dy > 0 and "上" or "下" end
    if (dx * dx + dy * dy) < (WHEEL_R * 0.3) * (WHEEL_R * 0.3) then dir = "中" end
    print(TAG .. " WHEEL pos=" .. s(x) .. "," .. s(y) .. " d=" .. s(dx) .. "," .. s(dy) .. " → " .. dir)
    send("轮盘" .. dir)
  end)
end

function OnInit()
  script:EnableUpdate(true)
  -- 踩坑.md P5：CursorEvent 要求祖先容器 showCursor=true，否则静默失效
  local ok, err = pcall(function() script.object.showCursor = true end)
  print(TAG .. " showCursor ok=" .. tostring(ok) .. " err=" .. s(err))

  out = script.object:FindChild("OutPanel")
  timerBox = script.object:FindChild("TimerBox")
  if out == nil then print(TAG .. " ERR 找不到 OutPanel") end
  if timerBox == nil then print(TAG .. " ERR 找不到 TimerBox") end

  log("=== 联机指令探针 · 开局计时 ===")
  setIdLine("本客户端 = 令牌 " .. s(token) .. "（座位 " .. s(readSlot()) .. "）")
  refreshTimer()

  pcall(function()
    script:RegisterCustomVariableChangedHandler(Enum.CustomVariableEntityType.PlayerSelf, "Slot", function()
      slot = readSlot()
      print(TAG .. " SLOT变 slot=" .. s(slot))
      setIdLine("本客户端 = P" .. s(slot))
    end)
  end)

  bindClick("轻攻击区", "轻攻击")
  bindClick("重攻击区", "重攻击")
  bindPad()

  script:RegisterServerSignalHandler("CmdOut", function(name, params)
    local whoSlot = tonumber(params and params[1])
    local cmd = params and params[3]
    local ts = tonumber(params and params[4])
    local whoToken = tonumber(params and params[5])
    local mine = (whoToken ~= nil and whoToken == token)   -- ★ 靠令牌认自己
    local delta = t - (ts or t)
    local who = mine and ("我(令牌" .. s(token) .. ")") or ("对方(令牌" .. s(whoToken) .. ")")
    if whoSlot and whoSlot > 0 then who = who .. " 座位P" .. s(whoSlot) end
    print(TAG .. " RECV mine=" .. tostring(mine) .. " whoSlot=" .. s(whoSlot) .. " whoToken=" .. s(whoToken)
      .. " seq=" .. s(params and params[2]) .. " cmd=" .. s(cmd)
      .. " sendT=" .. fmt(ts) .. " recvT=" .. fmt(t) .. " delta=" .. fmt(delta))
    log(who .. " 点「" .. s(cmd) .. "」 发出 @" .. fmt(ts) .. "s → 我收到 @" .. fmt(t) .. "s（差 " .. fmt(delta) .. "s）")
  end)

  print(TAG .. " ready")
end

function OnUpdate(dt)
  t = t + (tonumber(dt) or 0)
  refreshTimer()
end
