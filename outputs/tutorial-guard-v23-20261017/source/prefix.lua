GF_RAW_ASSET_TABLES=true
GF_ASSET_PRELOAD_AT_START=false
GF_ASSET_PROFILE='raw-literal-tables'
GF_RELEASE_ID='structure-20261011-furina-candidate'
GF_PERF_ENABLED=true
GF_FPS_VISIBLE=false
GF_FIXED_BODY_SCALE=true
-- Temporary native comparison: scene loading and exhaustion fallback remain.
GF_POOL_BACKGROUND_GROWTH=false
GF_BATTLE_IMAGE_POOL=16000
GF_MOBILE_BATTLE_IMAGE_POOL=12000
GF_DYNAMIC_IMAGE_TEMPLATE_INDEX=1073741845
GF_FIRST_SCENE='intro'
GF_FIRST_ARGS={chars={'raidenshogun','nahida'},mode='demo',cpu={2,2},rounds=2,time=99,seed=21}
GF_SETTINGS={quality='lo'}
-- Dual pool production client 3e508011db14
GF_BUILD='modular-source-existing-rules' 
local __loaders, __loaded = {}, {}
local function require(name)
 local m=__loaded[name]
 if m==nil then
  local f=__loaders[name]
  if not f then error('module not bundled: '..tostring(name)) end
  m=f(); __loaded[name]=m
 end
 return m
end
GF_REQUIRE=require

