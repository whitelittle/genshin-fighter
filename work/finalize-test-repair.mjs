import{readFileSync as read,writeFileSync as write}from'node:fs';
const out=process.env.REPAIR_OUT||'outputs/test-repair-v1',save=JSON.parse(read(out+'/fighter.save.json'));
function find(n,name){if(n.name===name)return n;for(const c of n.children||[]){const r=find(c,name);if(r)return r;}}
for(const name of['LoadingScreen','LoadingBlack']){const n=find(save.assets.server.root,name);for(const t of Object.values(n.transformByPlatform)){t.anchorMin={x:0,y:0};t.anchorMax={x:1,y:1};t.offset={x:0,y:0};t.size={x:0,y:0};}}
write(out+'/fighter.save.json',JSON.stringify(save));
const sim=structuredClone(save);sim.assets.scripts[0].source=sim.assets.scripts[0].source.replace('local PIXEL_TEMPLATE_INDEX=1073741845','local PIXEL_TEMPLATE_INDEX=0');write(out+'/simulator.save.json',JSON.stringify(sim));console.log('STRETCH_LOADING_READY');
