import {readFileSync,writeFileSync} from 'node:fs';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {renderPaintPng} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';
for(const mode of ['solo','online']){
 const out=`outputs/demo-${mode}-light`,s=createStudio(JSON.parse(readFileSync(out+'/fighter.save.json')));s.playStart({playerCount:mode==='online'?2:1});s.playStep(1/30,{observe:false});
 const r=s.playGet({view:true,paint:true});console.log(JSON.stringify({mode,logs:r.logs.slice(-10),status:r.scene.nodes.find(n=>n.name==='Status')?.text,stats:r.scene.nodes.find(n=>n.name==='Stats')?.text}));
 writeFileSync(out+'/开局.png',renderPaintPng(r.paint,r.canvasWidth,r.canvasHeight).data);
}
