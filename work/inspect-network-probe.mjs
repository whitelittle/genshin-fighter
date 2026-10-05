import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
const studio=createStudio();const result=studio.importData('gia',readFileSync('C:/Users/Cheng/Desktop/联机指令探针_输入UI.gia').toString('base64'),'联机指令探针_输入UI.gia');
const exported=studio.exportData('save');const data=JSON.parse(Buffer.from(exported.data,exported.encoding).toString('utf8'));
mkdirSync('outputs/network-probe-inspection',{recursive:true});writeFileSync('outputs/network-probe-inspection/imported.save.json',JSON.stringify(data,null,2));
const scripts=data.assets?.scripts||data.scripts||[];
for(const [i,script] of scripts.entries())writeFileSync('outputs/network-probe-inspection/script-'+i+'.lua',script.source||'');
console.log(JSON.stringify({warnings:result.warnings||result.snapshot?.migrationWarnings,meta:data.meta,scripts:scripts.map(({source,...rest})=>({...rest,sourceLength:source.length})),serverLogic:data.serverLogic||data.assets?.server?.serverLogic},null,2));
function walk(n){if(n.text)console.log(JSON.stringify({name:n.name,text:n.text}));for(const c of n.children||[])walk(c);}
for(const a of Object.values(data.assets||{}))if(a?.root)walk(a.root);
studio.playStart();studio.playStep(1/30);studio.playClick('轻攻击区');const state=studio.playGet({view:true});console.log(JSON.stringify({logs:state.logs.slice(-10)},null,2));
