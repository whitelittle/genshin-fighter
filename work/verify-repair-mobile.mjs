import{readFileSync as read,writeFileSync as write}from'node:fs';import assert from'node:assert/strict';
import{createStudio}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import{renderPaintPng}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';
const out=process.env.REPAIR_OUT||'outputs/test-repair-v1',save=JSON.parse(read(out+'/simulator.save.json')),results=[];
for(const canvasId of['mobile-19.5-9','mobile-4-3']){
 const s=createStudio(save);s.playStart({playerCount:2,canvasId});
 const get=()=>{const r=s.playGet({view:true});assert(!r.logs.some(l=>['error','lua-error'].includes(l.level)||/ERROR|加载失败/.test(l.text||'')),JSON.stringify(r.logs.slice(-5)));return r;};
 const has=n=>get().scene.nodes.some(x=>x.name===n),step=n=>{for(let k=0;k<n;k++)s.playStep(1/60,{observe:false});};
 const until=(p,label)=>{for(let k=0;k<16000;k+=30){if(p())return;step(30);}throw Error('timeout '+label);},settle=()=>until(()=>!has('LoadingText'),'settle');
 const click=(p,name)=>{s.playSetView(p);s.playClick(name,{observe:false});step(1);};
 settle();for(let p=1;p<=2;p++){click(p,'StartDuelHit');settle();}
 for(let p=1;p<=2;p++)for(const n of[p===1?1:2,3,5]){click(p,'GridCard'+n);settle();s.playSetView(3-p);settle();}
 for(let p=1;p<=2;p++){click(p,'ReadyConfirm');}
 until(()=>has('Timer')&&!has('LoadingText'),'battle');step(120);const r=s.playGet({view:true,paint:true});
 for(const n of['Stick1','Light','Heavy','Skill','Ultimate','BattleTeam11Plate','BattleTeam23Plate'])assert(r.scene.nodes.some(x=>x.name===n),n);
 const stage=r.scene.nodes.filter(x=>/^StagePx\d+$/.test(x.name));const sceneReport=JSON.parse(read(out+'/scene-report.json'));assert(sceneReport.countries.some(x=>x.rectangles===stage.length),'scene count does not match any fitted candidate');assert(stage.length<=sceneReport.budgetPerScene,'scene budget exceeded');
 let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;
 for(const p of stage){let x=p.matrix.tx,y=p.matrix.ty,w=p.sourceWidth*Math.abs(p.matrix.a),h=p.sourceHeight*Math.abs(p.matrix.d),parent=r.scene.nodes.find(n=>n.id===p.parent);while(parent){x=parent.matrix.a*x+parent.matrix.tx;y=parent.matrix.d*y+parent.matrix.ty;w*=Math.abs(parent.matrix.a);h*=Math.abs(parent.matrix.d);parent=r.scene.nodes.find(n=>n.id===parent.parent);}minX=Math.min(minX,x-w/2);maxX=Math.max(maxX,x+w/2);minY=Math.min(minY,y-h/2);maxY=Math.max(maxY,y+h/2);}
 write(out+'/'+canvasId+'-battle.png',renderPaintPng(r.paint,r.canvasWidth,r.canvasHeight).data);
 assert(minX<=1&&maxX>=r.canvasWidth-1&&minY<=1&&maxY>=r.canvasHeight-1,'scene does not cover canvas');
 write(out+'/'+canvasId+'-battle.png',renderPaintPng(r.paint,r.canvasWidth,r.canvasHeight).data);results.push({canvasId,fullSceneCoverage:true,touchAndRosterHUDPresent:true,images:stage.length});console.log('MOBILE_BATTLE_PASS',canvasId);s.playStop();
}
write(out+'/mobile-verification.json',JSON.stringify({simulatorOnly:true,results,deviceVerified:false},null,2));
