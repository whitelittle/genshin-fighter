import fs from 'node:fs';
import assert from 'node:assert/strict';
import {exportGia,importGia,validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
// Device finding (083731): crash exactly when loading ends; setHeavy('battle') activates ~934k stage block glyphs in one
// frame. T3 reveals the stage behind the black loading screen REVEAL_STEP rows per frame; the counter on screen at the
// moment of a crash measures how much text the phone can hold.
const REVEAL_STEP=Number(process.env.REVEAL_STEP||64);
const base=JSON.parse(fs.readFileSync('work/training-room-runtime-text-latest.json'));
const save=JSON.parse(fs.readFileSync(base.out+'/simulator.save.json'));
const native=JSON.parse(fs.readFileSync(base.out+'/fighter.save.json'));
let lua=native.assets.scripts[0].source;
const replaceOnce=(from,to)=>{assert.equal(lua.split(from).length,2,'anchor: '+from.slice(0,70));lua=lua.replace(from,()=>to);};

replaceOnce(' loadingTotal=loadingTotal+#loadingQueue+#loadingUnload\n',` resourceGate.loader.reveal=nil
 if mode=='battle'then local frame=resourceGate.stageFrame();resourceGate.loader.reveal={n=1,total=#frame.chunks,step=${REVEAL_STEP}};loadingTotal=loadingTotal+math.ceil(#frame.chunks/${REVEAL_STEP})+1 end
 loadingTotal=loadingTotal+#loadingQueue+#loadingUnload
`);
replaceOnce(`   if paint then Collision.stagePaintKey=paint.key;local c=resourceGate.textNodes(rootNode('CountryStage'));c.frame=paint.frame;c.scale=paint.scale end
   return false end`,`   if paint then Collision.stagePaintKey=paint.key;local c=resourceGate.textNodes(rootNode('CountryStage'));c.frame=paint.frame;c.scale=paint.scale end
   local rv=resourceGate.loader.reveal
   if rv and rv.n<=rv.total then
    local parent=rootNode('CountryStage');local c=resourceGate.textNodes(parent)
    if not rv.started then for i=1,rv.total do local node=c.nodes[i];if node then node:SetVisible(false)end end;parent:SetActive(true);rv.started=true
    else for i=rv.n,math.min(rv.total,rv.n+rv.step-1)do local node=c.nodes[i];if node then node:SetVisible(true)end end;rv.n=rv.n+rv.step end
    resourceGate.loader.yield=true;loadingDone=loadingDone+1;return true
   end
   return false end`);
replaceOnce("   if not loadingWork()then loadingState='complete';break end\n","   if not loadingWork()then loadingState='complete';break end\n   if resourceGate.loader.yield then resourceGate.loader.yield=nil;break end\n");
replaceOnce("'PAINT' or string.upper(tostring(loadingState))","'PAINT' or(resourceGate.loader.reveal and resourceGate.loader.reveal.n<=resourceGate.loader.reveal.total and 'REVEAL' or string.upper(tostring(loadingState)))");
replaceOnce("loadingLabel.text=string.format('T2 %s","loadingLabel.text=string.format('T3 %s");
replaceOnce("+(resourceGate.loader.textCreate or 0));loadingLabel:SetVisible(true)","+(resourceGate.loader.textCreate or 0))..(resourceGate.loader.reveal and string.format(' | reveal %d/%d',math.min(resourceGate.loader.reveal.n-1,resourceGate.loader.reveal.total),resourceGate.loader.reveal.total)or'');loadingLabel:SetVisible(true)");

const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date()).map(v=>[v.type,v.value]));
const stamp=p.year+p.month+p.day+'_'+p.hour+p.minute+p.second,out='outputs/training-room-reveal-diagnostic-'+stamp,name='gpt_'+stamp+'_训练室分批显示诊断_A';
fs.mkdirSync(out,{recursive:true});
for(const s of native.assets.scripts){s.source=lua;s.filename=name+'.lua';s.path=name+'.lua';}
native.assets.server.root.name=name;native.assets.server.meta.name=name;native.assets.server.meta.giaFileName=name+'.gia';
native.meta={...native.meta,name:'训练室版：分批显示诊断'};
const a=exportGia(native.assets.server,{scripts:native.assets.scripts});assert(validateServerGiaCompatibility(a.buffer).valid);
fs.writeFileSync(out+'/'+name+'.gia',a.buffer);fs.writeFileSync(out+'/fighter.save.json',JSON.stringify(native));fs.writeFileSync(out+'/完整游戏.lua',lua);
const aa=importGia(a.buffer,name+'.gia');assert.equal(aa.scripts[0].source,lua);
save.meta={...save.meta,name:native.meta.name};save.assets.server=aa.project;save.assets.scripts=aa.scripts;
for(const s of save.assets.scripts){const hits=[];const walk=n=>{if((n.scriptMappingIds||[]).includes(s.guid))hits.push(n);for(const c of n.children||[])walk(c);};walk(aa.project.root);assert.equal(hits.length,1);s.controlId=hits[0].id;}
fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(save));
const report={base:base.out,cTemplate:base.cName,revealStep:REVEAL_STEP,sourceBytes:Buffer.byteLength(lua),giaABytes:a.buffer.length,deviceVerified:false};
fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2));
fs.writeFileSync(out+'/实机测试说明.md',`# 训练室分批显示诊断（T3）\n\n083731 在读条结束一刻闪退：加载完成时训练室约 93 万个方块字形在同一帧激活。本版在黑屏下先隐藏全部训练室文字，再每帧显示 ${REVEAL_STEP} 块，诊断行末尾显示 reveal 已显示/总数，全部显示后才关闭黑屏。\n\n## 导入\n\nC 沿用已导入的 ${base.cName}.gia，不用重新导入。双方 A 换成 ${name}.gia，PIXEL_TEMPLATE_INDEX 和 TEXT_TEMPLATE_INDEX 照上次填写。\n\n## 观察\n\n- 若在 REVEAL 中途闪退：请记下闪退前最后看到的 reveal 数字，这就是手机能承受的大约文字量。\n- 若 REVEAL 走完并进入战斗：一次性激活的瞬时尖峰是原因，正式版可以分批显示。请继续观察战斗帧率、三局切换和回到选人。\n`);
fs.writeFileSync('work/training-room-reveal-diagnostic-latest.json',JSON.stringify({out,name,stamp,base:base.out,cName:base.cName},null,2));
console.log(JSON.stringify({out,name,...report}));
