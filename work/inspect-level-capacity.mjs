import {readFileSync} from 'node:fs';
const file='C:/Users/Cheng/AppData/LocalLow/miHoYo/原神/BeyondLocal/101816246/Beyond_Local_Save_Level/1073741844/1073741844.gil';
const b=readFileSync(file);
const names=['AnimationProbe','CombatDemoV01','FighterSoloDemo_ImportFix','FighterOnlineDemo_ImportFix','FighterOnlineRollbackTest','FighterDemo'];
const occurrences={};
for(const name of names){const needle=Buffer.from(name);let at=0,count=0;while((at=b.indexOf(needle,at))!==-1){count++;at+=needle.length;}occurrences[name]=count;}
const save=JSON.parse(readFileSync('outputs/demo-online-light-rollback/fighter.save.json','utf8'));
let total=0,sprites=0;const walk=n=>{total++;if(/^P\d+$/.test(n.name))sprites++;for(const c of n.children||[])walk(c);};walk(save.assets.server.root);
console.log(JSON.stringify({levelBytes:b.length,MB:b.length/1e6,MiB:b.length/1048576,nameOccurrences:occurrences,rollbackTemplate:{totalControls:total,spriteImages:sprites},note:'Binary string matches are evidence of names only, not decoded asset counts.'},null,2));
