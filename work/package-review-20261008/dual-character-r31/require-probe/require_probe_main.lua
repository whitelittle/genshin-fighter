local a=require('default_import_file/require_probe_a.lua')
local b=require('default_import_file/require_probe_b.lua')
assert(a.value==17 and b.read()==17)
a.value=29
assert(b.read()==29 and require('default_import_file/require_probe_a.lua')==a)
print('REQUIRE PROBE PASS')
