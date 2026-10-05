import fs from 'node:fs';
import assert from 'node:assert/strict';
import {exportGia,importGia,validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
// Device finding (083731, T3): crash when the accumulated training-room text (~934k block glyphs) is nearly all shown.
// T4 = 083731 plus unloading while loading battle: menu text art (HomeBust*, GridFace*) is emptied and its Lua rich-text
// strings dropped, and each stage chunk's cached rich-text string is dropped once it is on its node. Menu art repaints
// on return because every cache that would skip the repaint is reset.
const base=JSON.parse(fs.readFileSync('work/training-room-runtime-text-latest.json'));
const save=JSON.parse(fs.readFileSync(base.out+'/simulator.save.json'));
const native=JSON.parse(fs.readFileSync(base.out+'/fighter.save.json'));
let lua=native.assets.scripts[0].source;
const replaceOnce=(from,to)=>{assert.equal(lua.split(from).length,2,'anchor: '+from.slice(0,70));lua=lua.replace(from,()=>to);};

replaceOnce(' resourceGate.loader.textCreate=0\n',` if mode=='battle'then
  local s=resourceGate.loader.stats;s.unloadedText=0;s.unloadedGlyphBoxes=0
  for name,c in pairs(resourceGate.textArtCache)do if c.frame and(string.match(name,'^HomeBust%d$')or string.match(name,'^GridFace%d+$'))then
   for i,node in pairs(c.nodes)do if node.text~=''then node.text='';s.unloadedGlyphBoxes=s.unloadedGlyphBoxes+1 end;node:SetVisible(false);local chunk=c.frame.chunks[i];if chunk then chunk.text=nil end end
   c.frame=nil;c.scale=nil;s.unloadedText=s.unloadedText+1
  end end
  resourceGate.homePaintKeys={};gridRoles={}
 end
 resourceGate.loader.textCreate=0
`);
replaceOnce('resourceGate.paintTextChunk(parent,paint.frame,paint.scale,n);resourceGate.loader.stats.painted=resourceGate.loader.stats.painted+1 end',
 'resourceGate.paintTextChunk(parent,paint.frame,paint.scale,n);paint.frame.chunks[n].text=nil;resourceGate.loader.stats.painted=resourceGate.loader.stats.painted+1 end');
replaceOnce("loadingLabel.text=string.format('T2 %s","loadingLabel.text=string.format('T4 %s");
replaceOnce("+(resourceGate.loader.textCreate or 0));loadingLabel:SetVisible(true)","+(resourceGate.loader.textCreate or 0))..string.format(' | unload %d/%d',s.unloadedText or 0,s.unloadedGlyphBoxes or 0);loadingLabel:SetVisible(true)");

const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date()).map(v=>[v.type,v.value]));
const stamp=p.year+p.month+p.day+'_'+p.hour+p.minute+p.second,out='outputs/training-room-unload-'+stamp,name='gpt_'+stamp+'_训练室边卸边加_A';
fs.mkdirSync(out,{recursive:true});
for(const s of native.assets.scripts){s.source=lua;s.filename=name+'.lua';s.path=name+'.lua';}
native.assets.server.root.name=name;native.assets.server.meta.name=name;native.assets.server.meta.giaFileName=name+'.gia';
native.meta={...native.meta,name:'训练室版：边卸边加'};
const a=exportGia(native.assets.server,{scripts:native.assets.scripts});assert(validateServerGiaCompatibility(a.buffer).valid);
fs.writeFileSync(out+'/'+name+'.gia',a.buffer);fs.writeFileSync(out+'/fighter.save.json',JSON.stringify(native));fs.writeFileSync(out+'/完整游戏.lua',lua);
const aa=importGia(a.buffer,name+'.gia');assert.equal(aa.scripts[0].source,lua);
save.meta={...save.meta,name:native.meta.name};save.assets.server=aa.project;save.assets.scripts=aa.scripts;
for(const s of save.assets.scripts){const hits=[];const walk=n=>{if((n.scriptMappingIds||[]).includes(s.guid))hits.push(n);for(const c of n.children||[])walk(c);};walk(aa.project.root);assert.equal(hits.length,1);s.controlId=hits[0].id;}
fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(save));
const report={base:base.out,cTemplate:base.cName,sourceBytes:Buffer.byteLength(lua),giaABytes:a.buffer.length,deviceVerified:false};
fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2));
fs.writeFileSync(out+'/实机测试说明.md',`# 训练室边卸边加（T4）\n\n在 083731 的基础上，进入战斗加载时清空首页大图和选人头像的文字，并丢掉它们在 Lua 里的富文本缓存；训练室每块文字画到控件上后，也立刻丢掉 Lua 里的那份富文本。回到菜单时整幅重画。训练室画质不变，读条流程与 083731 相同。\n\n## 导入\n\nC 沿用已导入的 ${base.cName}.gia。双方 A 换成 ${name}.gia，PIXEL_TEMPLATE_INDEX 和 TEXT_TEMPLATE_INDEX 照上次填写。\n\n## 观察\n\n诊断行末尾的 unload 卸载组数/清空文字框数，进战斗时应为非零。请记录能否进入战斗、三局切换和回到选人后头像是否正常。若仍在读条结束时闪退，说明这台手机的余量不够，需要降低训练室分辨率。\n`);
fs.writeFileSync('work/training-room-unload-latest.json',JSON.stringify({out,name,stamp,base:base.out,cName:base.cName},null,2));
console.log(JSON.stringify({out,name,...report}));
