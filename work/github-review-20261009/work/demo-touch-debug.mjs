import {readFileSync} from 'node:fs';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
const save=JSON.parse(readFileSync('outputs/demo-solo-light/fighter.save.json'));save.assets.scripts[0].source=save.assets.scripts[0].source.replace("local function stick(d)","local function stick(d) print('STICK '..d)");
console.log(JSON.stringify(save.assets.server.root.transformByPlatform));console.log(JSON.stringify(save.assets.server.root.children[0].transformByPlatform));
const s=createStudio(save);s.playStart();let r=s.playGet({view:true});const n=r.scene.nodes.find(x=>x.name==='Stick5');const x=n.matrix.tx+r.canvasWidth/2,y=n.matrix.ty+r.canvasHeight/2;console.log({canvas:[r.canvasWidth,r.canvasHeight],node:n,x,y});
for(const [type,px,py]of[['down',x,y],['move',x,y-48],['move',x+48,y-48],['move',x+48,y]]){s.playPointer(type,px,py,{observe:false});console.log(type,s.playGet({view:true}).logs.slice(-8));}s.playClick('Light');s.playStep(1/30);console.log(s.playGet({view:true}).logs.slice(-15));
