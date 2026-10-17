import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {exportGia,validateServerGiaCompatibility,importGia} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const out='outputs/native-text-length-probe-20261005';fs.mkdirSync(out,{recursive:true});
const save=JSON.parse(fs.readFileSync('outputs/native-text-calibration-20261005/simulator.save.json'));
const root=save.assets.server.root,host=root.children[0];
root.name='gpt_20261005_文字长度缩放校准';root.guid=1073940000;host.guid=1073940001;
const upper='<b><color=#FF0000FF>████</color><color=#00FF00FF>████</color></b>';
const lower=upper.replaceAll('FF','ff');
// Empty color spans increase parser input without changing the visible glyph grid.
// This isolates string length; it does not establish a native limit for real portraits.
const padded=n=>upper+'<color=#FFFFFFFF></color>'.repeat(Math.ceil(n/24));
const cases=[['Uppercase',upper,1],['Lowercase',lower,1],['Uppercase scale 0.25',upper,.25],['Lowercase scale 0.25',lower,.25],...[1024,8192,32768,131072].map(n=>['Uppercase padding '+n,padded(n),1])];
const quote=s=>JSON.stringify(s).replace(/[^\x00-\x7f]/gu,c=>Array.from(Buffer.from(c)).map(v=>'\\'+String(v).padStart(3,'0')).join(''));
const assignments=[];
for(const n of host.children){n.guid+=20000;n.id='length_'+n.guid;}
for(let i=0;i<cases.length;i++){
 const [label,value,scale]=cases[i];
 host.children.find(n=>n.name==='Label'+i).text=(i+1)+'. '+label+' | bytes '+Buffer.byteLength(value);
 for(const name of ['Static'+i,'Dynamic'+i]){
  const node=host.children.find(n=>n.name===name);node.kind='textbox';node.text=name.startsWith('Static')?value:'WAIT';
  // Apply scales at runtime for both columns, isolating SetLocalScale from parsing.
  assignments.push(`script.object:FindChild('${name}'):SetLocalScale(${scale},${scale},1)`);
 }
 assignments.push(`script.object:FindChild('Dynamic${i}').text=${quote(value)}`);
}
host.children.find(n=>n.name==='Header').text='TEXT LENGTH / SCALE: LEFT STATIC, RIGHT LUA';
host.children.find(n=>n.name==='Hint').text='Every row should show RED then GREEN. Rows 3-4 are smaller. No B / network needed.';
const lua='function OnStart()\n'+assignments.join('\n')+'\nprint("TEXT-LENGTH-PROBE READY")\nend';
save.assets.scripts[0].source=lua;save.assets.scripts[0].guid=1073940999;
save.assets.server.meta={...save.assets.server.meta,name:root.name,giaFileName:root.name+'.gia',giaFileId:root.guid};
save.meta.name='文字长度与缩放独立校准';
const studio=createStudio(save);studio.playStart();const state=studio.playGet({view:true});
assert.equal(state.logs.filter(l=>['error','lua-error'].includes(l.level)).length,0);studio.playStop();
const result=exportGia(save.assets.server,{scripts:save.assets.scripts});assert(validateServerGiaCompatibility(result.buffer).valid);
assert(importGia(result.buffer,root.name+'.gia').scripts.some(s=>s.source===lua));
fs.writeFileSync(out+'/'+root.name+'.gia',result.buffer);fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(save));
fs.writeFileSync(out+'/verification.json',JSON.stringify({structuralCheck:true,nativeVisualVerified:false,requiresB:false,requiresNetwork:false,cases:cases.map(([label,value,scale])=>({label,utf8Bytes:Buffer.byteLength(value),scale})),limitation:'Padding uses empty color spans to isolate length. Actual portrait layout and glyph-count limits still require separate native verification.'},null,2));
console.log('TEXT_LENGTH_PROBE_STRUCTURAL_PASS');
