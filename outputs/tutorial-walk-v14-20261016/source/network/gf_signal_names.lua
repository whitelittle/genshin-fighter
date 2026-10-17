__loaders['gf_signal_names']=function()
-- Optional map-specific binding at the import boundary. Protocol names stay stable.
local S={}
function S.resolve(name)
    return GF_SIGNAL_BINDINGS and GF_SIGNAL_BINDINGS[name] or name
end
return S
end
