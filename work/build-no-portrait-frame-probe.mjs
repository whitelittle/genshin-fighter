import fs from 'node:fs';
import assert from 'node:assert/strict';
import {exportGia,importGia,validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
// Single-variable probe: the 075742 training-room A (empty in the editor) minus the 10 PortraitFrame* images,
// the only controls in A whose GUIDs (1078000000+) were hand-assigned outside the original ranges.
const base='outputs/training-room-runtime-text-20261005_075742';
const native=JSON.parse(fs.readFileSync(base+'/fighter.save.json'));
let removed=[];
const strip=n=>{n.children=(n.children||[]).filter(c=>{if(/^PortraitFrame/.test(c.name)){removed.push(c.guid);return false}return true});n.children.forEach(strip);};
strip(native.assets.server.root);
assert.equal(removed.length,10);
const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date()).map(v=>[v.type,v.value]));
const stamp=p.year+p.month+p.day+'_'+p.hour+p.minute+p.second,out='outputs/no-portrait-frame-probe-'+stamp,name='gpt_'+stamp+'_训练室去头像框_A';
fs.mkdirSync(out,{recursive:true});
for(const s of native.assets.scripts){s.filename=name+'.lua';s.path=name+'.lua';}
native.assets.server.root.name=name;native.assets.server.meta.name=name;native.assets.server.meta.giaFileName=name+'.gia';
const a=exportGia(native.assets.server,{scripts:native.assets.scripts});assert(validateServerGiaCompatibility(a.buffer).valid);
const back=importGia(a.buffer,name+'.gia');assert.equal(back.scripts[0].source,native.assets.scripts[0].source);
fs.writeFileSync(out+'/'+name+'.gia',a.buffer);
fs.writeFileSync(out+'/fighter.save.json',JSON.stringify(native));
let controls=0,maxGuid=0;const count=n=>{controls++;maxGuid=Math.max(maxGuid,n.guid||0);for(const c of n.children||[])count(c);};count(native.assets.server.root);
const report={base,removedGuids:removed,initialClientControls:controls-1,maxGuid,sourceBytes:Buffer.byteLength(native.assets.scripts[0].source),giaBytes:a.buffer.length};
fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2));
fs.writeFileSync(out+'/说明.md',`# 训练室去头像框探针\n\n与075742训练室运行时文字版A相同，只删除两侧大头像的10个PortraitFrame图片控件（GUID 1078000000–1078000009，是A中唯一手动分配到1078号段的控件）。控件${report.initialClientControls}个，主Lua ${report.sourceBytes}字节不变。\n\n导入后看编辑器是否出现默认黑屏：\n- 出现：这10个控件是A为空的原因。\n- 仍为空：原因在其余446个大头像TextArt或其他差异。\n\n运行时头像边框不显示，其他逻辑不变（脚本按名字查找边框，找不到时跳过）。\n`);
console.log(JSON.stringify({out,name,...report,removedGuids:undefined}));
