local TEXT_TEMPLATE_INDEX=1078200001 -- C outer container actual index
local rows,created,timer,failed={},0,0,false
local function status(s)local n=script.object:FindChild('NativeBootProbe');n.text=s;n:SetVisible(true);n:SetAsFirstSibling()end
function OnInit()status('LUA INIT OK / waiting for module');script:EnableUpdate(true)end
function OnStart()
 local ok,result=pcall(require,'default_import_file/DynamicTextRows_20261005_042532')
 if not ok then failed=true;status('MODULE ERROR: '..tostring(result));return end
 rows=result.rows;status('MODULE OK / 0 / '..#rows);script:EnableUpdate(true)
end
function OnUpdate(dt)
 if failed or #rows==0 or created>=#rows then return end
 timer=timer+dt;if timer<0.1 then return end;timer=0
 local ok,err=pcall(function()
  local row=rows[created+1]
  local box=game.InstantiateClientUIControl(TEXT_TEMPLATE_INDEX,script.object)
  if not box then error('C template not found: '..TEXT_TEMPLATE_INDEX)end
  local n=box:FindChild('TextPixel');if not n then error('C missing TextPixel')end
  box.name='DynamicText'..(created+1);box:SetAnchoredPosition(row.x,row.y)
  n.text=row.text;n:SetVisible(true);box:SetVisible(true)
  created=created+1;status((created==#rows and 'DYNAMIC TEXT OK / 'or'CREATING / ')..created..' / '..#rows)
 end)
 if not ok then failed=true;status('CREATE ERROR: '..tostring(err))end
end
