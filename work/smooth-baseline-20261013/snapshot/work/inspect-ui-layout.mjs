import{readFileSync}from'node:fs';
const save=JSON.parse(readFileSync(process.argv[2]||'outputs/midphase-final/base.save.json')),pattern=new RegExp(process.argv[3]||'^(TopPanel|Portrait[12]|StageTitle|Status|Energy[12]|Name[12])$');
function walk(n){const t=Object.values(n.transformByPlatform||{})[0];if(pattern.test(n.name)||(process.argv[3]==='HUD_NEAR'&&t&&Math.abs(t.offset?.x)>500&&t.offset?.y>280&&t.size?.x<160))console.log(JSON.stringify({name:n.name,kind:n.kind,color:n.imageColor,transform:t}));for(const c of n.children||[])walk(c);}
walk(save.assets.server.root);
if(process.argv[4]==='details'){function detail(n){if(pattern.test(n.name))console.log(JSON.stringify(n));for(const c of n.children||[])detail(c);}detail(save.assets.server.root);}
