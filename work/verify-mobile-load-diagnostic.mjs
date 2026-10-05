import fs from 'node:fs';import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {renderPaintPng} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';
const {out}=JSON.parse(fs.readFileSync(process.env.DIAG_LATEST||'work/mobile-load-diagnostic-latest.json'));
const save=JSON.parse(fs.readFileSync(out+'/simulator.save.json'));
const s=createStudio(save);s.playStart({playerCount:2,canvasId:'mobile-19.5-9'});
const get=()=>s.playGet({view:true});
const errors=()=>get().logs.filter(l=>['error','lua-error'].includes(l.level)||/RESOURCE ERROR|ERROR:/.test(l.text||''));
const has=n=>get().scene.nodes.some(x=>x.name===n);
const label=()=>get().scene.nodes.find(x=>x.name==='LoadingText')?.text;
const step=n=>{for(let i=0;i<n;i++)s.playStep(1/60,{observe:false});assert.equal(errors().length,0,JSON.stringify(errors()));};
const until=(p,l,max=40000)=>{for(let i=0;i<max;i+=10){if(p())return;step(10);}throw Error('Timeout '+l);};
const settled=()=>until(()=>!has('LoadingBar'),'settle');
const click=(p,n)=>{s.playSetView(p);const r=get();let node=r.scene.nodes.find(x=>x.name===n)||r.scene.nodes.find(x=>x.name===(n==='StartDuelHit'?'StartDuel':n));assert(node,n);let x=0,y=0;while(node){const ox=x,oy=y;x=node.matrix.a*ox+node.matrix.c*oy+node.matrix.tx;y=node.matrix.b*ox+node.matrix.d*oy+node.matrix.ty;node=r.scene.nodes.find(q=>q.id===node.parent);}s.playPointer('click',x,y,{observe:false});step(1);};
for(let p=1;p<=2;p++){s.playSetView(p);settled();assert(!label(),'diag text must stay hidden in menu');click(p,'StartDuelHit');settled();}
for(let p=1;p<=2;p++)for(const role of (p===1?[1,3,5]:[2,4,6])){s.playSetView(p);settled();click(p,'GridCard'+role);settled();s.playSetView(3-p);settled();}
click(1,'ReadyConfirm');step(60);click(2,'ReadyConfirm');s.playSetView(1);
const seen=[];let shot=false;const stageText=()=>get().scene.nodes.filter(x=>/^TextArt\d+$/.test(x.name)).length;let maxTextDuringCreate=0;
until(()=>{const t=label();if(t&&t!==seen[seen.length-1])seen.push(t);if(t&&/ CREATE /.test(t))maxTextDuringCreate=Math.max(maxTextDuringCreate,stageText());if(!shot&&t&&/CREATE/.test(t)){shot=true;const r=s.playGet({view:true,paint:true});fs.writeFileSync(out+'/simulator-mobile-diag-create.png',renderPaintPng(r.paint,r.canvasWidth,r.canvasHeight).data);}return has('Timer')&&!has('LoadingBar');},'battle');
const phases=[...new Set(seen.map(t=>t.split(' ')[/^(MOBILE|D4) /.test(t)?2:1]))];
assert(phases.includes('DECODE')&&phases.includes('CREATE'),JSON.stringify(phases));
assert(seen.some(t=>/create 4042\/4042/.test(t)),'final create count');
if(/D3|D4|D5|T1|T2|T3|T4/.test(seen[0]))assert(!has('GridCard1')&&!has('StartDuel'),'menu subtrees inactive in battle');
if(/T4/.test(seen[0]))assert(seen.some(t=>/unload [1-9]\d*\/[1-9]\d*$/.test(t)),'menu text unloaded: '+seen[seen.length-1]);
if(/T2|T3|T4/.test(seen[0]))assert(phases.includes('TEXT')&&seen.some(t=>/text 813\/813/.test(t)),'runtime text groups: '+seen[seen.length-1]);
if(/T3/.test(seen[0]))assert(phases.includes('REVEAL')&&seen.some(t=>/reveal (\d+)\/\1$/.test(t)),'staged reveal: '+seen[seen.length-1]);
let battleText=null;
if(/T1|T2|T3|T4/.test(seen[0])){assert.equal(maxTextDuringCreate,0,'text subtrees must be inactive while creating');step(30);battleText=stageText();assert(battleText>10000,'training room shown after load: '+battleText);}
s.playStop();
const result={simulatorOnly:true,deviceVerified:false,canvas:'mobile-19.5-9',phases,first:seen[0],last:seen[seen.length-1],samples:seen.length,maxTextDuringCreate,battleText};
fs.writeFileSync(out+'/diag-verification.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
