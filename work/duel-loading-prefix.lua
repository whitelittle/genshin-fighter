local loadingRegistry={}
local function loadingKey(parent)
 if parent.name=='Sprite' then return parent.parent.parent.name..'/Art/Sprite' end
 if parent.name=='Phoenix' then return parent.parent.name..'/Phoenix' end
 return parent.name
end
local function loadingFind(parent,name)
 local pool=loadingRegistry[loadingKey(parent)]
 return pool and pool[name] or parent:FindChild(name)
end
