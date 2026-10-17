import fs from 'node:fs';
import assert from 'node:assert/strict';
import {exportGia,importGia,validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
// Single-variable probe: the known-good 050817 A plus inert copies of the 052337 stage/portrait data lines,
// so the main Lua reaches the same 8.54MB as the failing builds while controls and logic stay unchanged.
const good=JSON.parse(fs.readFileSync('work/menu-art-return-latest.json')).out;
const big=fs.readFileSync(JSON.parse(fs.readFileSync('work/full-art-return-latest.json')).out+'/完整游戏.lua','utf8');
const native=JSON.parse(fs.readFileSync(good+'/fighter.save.json'));
let lua=native.assets.scripts[0].source;
const pick=prefix=>{const line=big.split('\n').find(l=>l.startsWith(prefix));assert(line);return line;};
const target=Number(process.env.SIZE_TARGET||0);
let pad=[pick('local Collision='),pick('local portraitData=')].map((line,i)=>'local __sizeProbe'+(i+1)+line.slice(line.indexOf('=')));
if(target){const filler=target-Buffer.byteLength(lua)-40;assert(filler>0);pad=['local __sizeProbe=[['+'#'.repeat(filler)+']]'];}
// Scoped block: adds no top-level locals to the main chunk.
lua='do\n'+pad.join('\n')+'\nend\n'+lua;
if(target)assert(Math.abs(Buffer.byteLength(lua)-target)<64);
const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date()).map(v=>[v.type,v.value]));
const stamp=p.year+p.month+p.day+'_'+p.hour+p.minute+p.second,out='outputs/script-size-probe-'+stamp,name='gpt_'+stamp+'_脚本体积探针'+(target?'_'+(target/1048576).toFixed(2)+'MiB':'')+'_A';
fs.mkdirSync(out,{recursive:true});
for(const s of native.assets.scripts){s.source=lua;s.filename=name+'.lua';s.path=name+'.lua';}
native.assets.server.root.name=name;native.assets.server.meta.name=name;native.assets.server.meta.giaFileName=name+'.gia';
const a=exportGia(native.assets.server,{scripts:native.assets.scripts});assert(validateServerGiaCompatibility(a.buffer).valid);
assert.equal(importGia(a.buffer,name+'.gia').scripts[0].source,lua);
fs.writeFileSync(out+'/'+name+'.gia',a.buffer);
let controls=0;const count=n=>{controls++;for(const c of n.children||[])count(c);};count(native.assets.server.root);
const report={base:good,initialClientControls:controls-1,sourceBytes:Buffer.byteLength(lua),baseSourceBytes:Buffer.byteLength(JSON.parse(fs.readFileSync(good+'/fighter.save.json')).assets.scripts[0].source),giaBytes:a.buffer.length};
fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2));
fs.writeFileSync(out+'/说明.md',`# 脚本体积探针\n\n与050817封面选人恢复版完全相同（控件${report.initialClientControls}个、逻辑不变），只在主Lua开头加入不执行的${target?'填充字符串':'训练室与大头像数据副本'}，使脚本从${report.baseSourceBytes}字节增至${report.sourceBytes}字节（打开为空的075742为8,544,053字节；8MiB=8,388,608字节）。\n\n导入后看界面编辑器是否正常显示050817的控件树与画面：\n- 也为空：脚本体积是原因，训练室数据需移出主脚本。\n- 正常：体积不是原因，问题在075742其他差异。\n`);
console.log(JSON.stringify({out,name,...report}));
