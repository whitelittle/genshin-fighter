import fs from 'node:fs';import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
const out='outputs/text-avatars-20261005';const findings=[];
for(const directory of ['outputs/loading-fix-20261005',out]){
 const save=JSON.parse(fs.readFileSync(directory+'/simulator.save.json'));const s=createStudio(save);s.playStart({playerCount:2});
 const state=()=>{const r=s.playGet({view:true});assert.equal(r.logs.filter(l=>['lua-error','error'].includes(l.level)||/RESOURCE ERROR/.test(l.text||'')).length,0,JSON.stringify(r.logs.slice(-4)));return r;};
 const has=name=>state().scene.nodes.some(n=>n.name===name);
 const step=n=>{for(let i=0;i<n;i++)s.playStep(1/60,{observe:false});};
 const settle=()=>{for(let i=0;i<4000;i+=10){if(!has('LoadingBar'))return;step(10);}throw Error('Loading timeout');};
 const click=(p,name)=>{s.playSetView(p);const r=state();let n=r.scene.nodes.find(x=>x.name===name);assert(n,'input '+name);let x=0,y=0;while(n){const ox=x,oy=y;x=n.matrix.a*ox+n.matrix.c*oy+n.matrix.tx;y=n.matrix.b*ox+n.matrix.d*oy+n.matrix.ty;n=r.scene.nodes.find(x=>x.id===n.parent);}s.playPointer('click',x,y,{observe:false});step(1);};
 s.playSetView(1);settle();assert(has('StartDuel'));const homeLogs=state().logs.filter(l=>/LOAD METRIC|LOAD SCHEDULE|TEXT APPLY/.test(l.text||''));
 if(directory===out){const arts=state().scene.nodes.filter(n=>n.name==='TextArt');assert.equal(arts.length,2);assert(arts.every(n=>n.text.startsWith('<b><color=#')&&n.text.includes('█')));assert(!state().scene.nodes.some(n=>/^HomePx\d/.test(n.name)));}
 for(let p=1;p<=2;p++){s.playSetView(p);settle();click(p,'StartDuel');settle();}
 s.playSetView(1);settle();const page1=state();if(directory===out){assert.equal(page1.scene.nodes.filter(n=>n.name==='TextArt').length,10);assert(!page1.scene.nodes.some(n=>/^IconPx\d/.test(n.name)));}
 click(1,'GridCard1');settle();if(directory===out){assert(state().scene.nodes.some(n=>n.name==='TextArt'&&n.text.includes('<color=#')));assert(!state().scene.nodes.some(n=>/^FacePx\d/.test(n.name)));}
 click(1,'PageNext');settle();if(directory===out){assert.equal(state().scene.nodes.filter(n=>n.name==='TextArt').length,10);}
 findings.push({directory:directory.split('/').pop(),homeLogs,allLogs:state().logs.filter(l=>/LOAD METRIC|LOAD SCHEDULE|TEXT APPLY/.test(l.text||'')),structuralCheck:true});s.playStop();
}
fs.writeFileSync(out+'/verification.json',JSON.stringify({simulatorOnly:true,homeAndBothSelectionPagesAndPreview:true,richTextVisualVerification:false,nativeTimingComparison:false,findings,deviceVerified:false},null,2));console.log('TEXT_AVATAR_LOADING_STRUCTURE_PASS');
