import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const out='outputs/fighter-online-v0.1';mkdirSync(out,{recursive:true});
const save=JSON.parse(readFileSync('outputs/fighter-v0.5/fighter.save.json'));
save.meta.name='原神格斗·双人联机版 v0.1';save.assets.scripts[0].source=readFileSync('work/fighter-online.lua','utf8');save.assets.scripts[0].path='lua/fighter-online.lua';
const refs=n=>Array.from({length:n},(_,i)=>({fromSignalParam:i}));
save.serverLogic={version:1,rules:[
 {id:'seats',signalName:'FighterHello',actions:[{kind:'sendClientScriptSignal',target:'Player1',signalName:'FighterSeat',params:[1]},{kind:'sendClientScriptSignal',target:'Player2',signalName:'FighterSeat',params:[2]}]},
 {id:'join',signalName:'FighterJoin',actions:[{kind:'sendClientScriptSignal',target:'AllPlayers',signalName:'FighterJoined',params:[]}]},
 {id:'inputs',signalName:'FighterInput',actions:[{kind:'sendClientScriptSignal',target:'AllPlayers',signalName:'FighterInputOut',params:refs(4)}]},
 {id:'states',signalName:'FighterState',actions:[{kind:'sendClientScriptSignal',target:'AllPlayers',signalName:'FighterStateOut',params:refs(2)}]},
]};
function walk(n){if(n.name==='Name1')n.text='刻晴 / 玩家1';if(n.name==='Name2')n.text='迪卢克 / 玩家2';if(n.name==='ArtNote')n.text='双人联机版 v0.1 / 同步战斗帧 · 暂停后切换视角对照';if(n.name==='LightText')n.text='轻攻击';for(const c of n.children||[])walk(c);}
walk(save.assets.server.root);
writeFileSync(out+'/fighter-online.save.json',JSON.stringify(save));writeFileSync(out+'/fighter-online.lua',save.assets.scripts[0].source);writeFileSync(out+'/server-logic.json',JSON.stringify(save.serverLogic,null,2));
const result=createStudio(save).exportData('gia-combined'),buffer=Buffer.from(result.data,result.encoding);const valid=validateServerGiaCompatibility(buffer);if(!valid.valid)throw Error(JSON.stringify(valid));writeFileSync(out+'/原神格斗_双人联机版.gia',buffer);
writeFileSync(out+'/build.json',JSON.stringify({giaCompatible:true,bytes:buffer.length,warnings:result.warnings,serverLogicIncludedInSave:true,serverLogicIncludedInGia:false},null,2));
console.log(JSON.stringify({bytes:buffer.length,warnings:result.warnings}));
