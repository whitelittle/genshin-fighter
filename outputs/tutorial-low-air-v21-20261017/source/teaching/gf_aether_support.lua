__loaders['gf_aether_support']=function()
-- Support-only asset provider. Deliberately absent from the playable roster.
return require('gf_character_assets').new(require('gf_aether_support_data'))
end
