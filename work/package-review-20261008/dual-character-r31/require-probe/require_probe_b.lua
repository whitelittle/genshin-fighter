local a=require('default_import_file/require_probe_a.lua')
return {read=function() return a.value end}
