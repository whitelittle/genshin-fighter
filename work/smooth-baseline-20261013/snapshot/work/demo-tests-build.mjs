import {readFileSync,writeFileSync} from 'node:fs';
let solo=readFileSync('work/fighter-verify.mjs','utf8').replaceAll('outputs/fighter-v0.5','outputs/demo-solo-light').replaceAll('gpt_fighter_v0.5.gia','原神格斗_单人AI_light.gia');
solo=solo.replace("high.playKey('KeyboardCraftspersonKey20Down'","high.playKey('KeyboardMoveRightKeyDown',{observe:false});high.playKey('KeyboardCraftspersonKey20Down'").replace("includes('100 / 81'),'overhead failed","includes('100 / 82'),'overhead failed");
solo=solo.replace('procedural placeholder figures, not approved character sprites','sampled existing character masters and four key poses per character');
writeFileSync('work/demo-regression.mjs',solo);
let net=readFileSync('work/fighter-online-verify.mjs','utf8').replaceAll('outputs/fighter-online-v0.1','outputs/demo-online-light').replace('fighter-online.save.json','fighter.save.json');
// Existing source and archived single-player delivery remain untouched.
writeFileSync('work/demo-net-regression.mjs',net);
