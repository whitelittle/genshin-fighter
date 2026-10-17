local ticks=0
local function mark(s)
 local n=script.object:FindChild('NativeBootProbe')
 if n then n.text=s;n:SetActive(true);n:SetVisible(true);n:SetAsFirstSibling()end
end
function OnInit()mark('LUA INIT OK');script:EnableUpdate(true)end
function OnStart()mark('LUA START OK');script:EnableUpdate(true)end
function OnUpdate(dt)ticks=ticks+1;mark('LUA UPDATE OK / '..ticks)end
