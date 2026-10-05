import fs from 'node:fs';import assert from 'node:assert/strict';import{createStudio}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
const out='outputs/network-node-sample5';fs.mkdirSync(out,{recursive:true});
let source=fs.readFileSync('outputs/midphase-final/gpt_20261004_191454_实机信号绑定修复.lua','utf8');
const anchor=' if not onlineReady or not rb then menuDraw();return end';assert.equal(source.split(anchor).length,2);
source=source.replace(anchor,` if not onlineReady or not rb then
  menuDraw()
  if menuMode=='select' and seat==0 then
   rootNode('SelectionHint').text='SEAT-PROBE-5 | Hello='..helloCount..' | SeatRx='..seatProbeCount..' | Slot='..seat..'\\nTX=信号_16 / RX=信号_15'
  end
  return
 end`);
const filename='gpt_20261004_节点图5_席位可见诊断.lua';fs.writeFileSync(out+'/'+filename,source);
const save=JSON.parse(fs.readFileSync('outputs/midphase-final/simulator.save.json'));save.assets.scripts[0].source=source;
const s=createStudio(save);s.playStart({playerCount:2});for(let i=0;i<150;i++)s.playStep(1/60,{observe:false});
for(const p of[1,2]){s.playSetView(p);const r=s.playGet({view:true});assert(!r.logs.some(l=>['error','lua-error'].includes(l.level)),'probe startup failed');}
s.playStop();
// Exercise the no-server path directly, without pretending a successful API call proves receipt.
source=source.replace("local menuMode='home'","local menuMode='select'");
const waiting=structuredClone(save);waiting.assets.scripts[0].source=source;waiting.serverLogic={version:1,rules:[]};const w=createStudio(waiting);w.playStart();for(let i=0;i<5000;i++)w.playStep(1/60,{observe:false});const state=w.playGet({view:true});assert(!state.logs.some(l=>['error','lua-error'].includes(l.level)));assert(state.scene.nodes.some(n=>n.name==='SelectionHint'&&n.text.includes('SEAT-PROBE-5')));w.playStop();
fs.writeFileSync(out+'/probe-verification.json',JSON.stringify({filename,normalTwoPlayerStartup:true,noServerHintUpdated:true,officialVerified:false},null,2));console.log(filename);
