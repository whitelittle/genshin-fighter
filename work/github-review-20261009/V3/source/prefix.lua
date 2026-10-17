GF_RELEASE_ID='r33-opt-E-20261008'
GF_PERF_ENABLED=true
GF_FIRST_SCENE='intro'
GF_FIRST_ARGS={chars={'raidenshogun','nahida'},mode='demo',cpu={2,2},rounds=2,time=99,seed=21}
GF_SETTINGS={quality='lo'}
-- Dual pool production client 3e508011db14
GF_BUILD='r33-opt-E-idle-hit-flash' 
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

