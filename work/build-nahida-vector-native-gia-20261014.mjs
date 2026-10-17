import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {createNode} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/ui/authoring.js';
import {exportGia,importGia,validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
import {renderPaintPng} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';

const out='outputs/nahida-18color-native-gia-20261014';
const data=JSON.parse(fs.readFileSync(out+'/native-geometry.json'));
const baseline=JSON.parse(fs.readFileSync('outputs/full-reinstall/simulator.save.json'));
const report=JSON.parse(fs.readFileSync(out+'/geometry-report.json'));
let guid=1076000000;
function node(kind,name,props={}){return createNode(kind,{name,id:'nv'+guid,guid:guid++,syncAllDevices:false,...props});}
function place(n,x,y,w,h,z=0,scale=1){for(const t of Object.values(n.transformByPlatform)){t.anchorMin={x:.5,y:.5};t.anchorMax={x:.5,y:.5};t.pivot={x:.5,y:.5};t.offset={x,y};t.size={x:w,y:h};t.scale={x:scale,y:scale,z:1};t.rotation={x:0,y:0,z};}return n;}
function color(hex){return (0xff000000|parseInt(hex.slice(1),16))>>>0;}
const root=node('server-container','草神18色矢量几何实验');
const stage=place(node('container','VectorStudyStage'),0,0,1600,900);
root.children.push(stage);
const host=place(node('container','闭合色块原生三角形'),0,-25,251,462,0,1.45);
const background=place(node('image','背景',{imageId:100001,imageColor:0xfff5f3ed}),0,0,1600,900);
stage.children.push(background,host);
for(let i=0;i<data.images.length;i++){
 const [x,y,w,h,angle,fill]=data.images[i];
 const n=node('image','VectorTriangle'+i,{imageId:100003,imageColor:color(fill),enableFill:true,fillType:'Horizontal',fillHorizontalType:'Left',fillAmount:.5});
 // A subpixel overlap compensates independent sprite antialiasing at mesh seams.
 place(n,x-data.w/2,y+data.h/2,w+1.2,h+.6,angle);
 host.children.push(n);
}
function label(name,text,y,size=23){const n=node('textbox',name,{text,fontSize:size,minimumFontSize:size,fontColor:0xff354139,bgColor:0,enableOutline:false,horizontalAlignment:'Middle',verticalAlignment:'Middle'});place(n,0,y,1500,40);stage.children.push(n);}
label('Title','草神 · 高清第一帧18色版 · 原生 GIA 回读模拟器',382,27);
label('Count',`${report.sourceClosedSubpaths} 个 SVG 闭合子路径 → ${data.images.length.toLocaleString('en-US')} 个原生三角形图片`,340,21);
label('Note','静态几何小样；未使用像素矩形或 PNG 替代。尚未验证真机。',-390,19);
// Authoring child lists are front-to-back, while SVG painting is back-to-front.
stage.children.reverse();host.children.reverse();
const save={format:baseline.format,version:baseline.version,meta:{name:root.name},activeAssetType:baseline.activeAssetType,serverLogic:{version:1,rules:[]},assets:{server:{...baseline.assets.server,root,meta:{...baseline.assets.server.meta,name:root.name,sourceFile:'',giaFileName:'草神_18色矢量几何实验.gia',giaFileId:root.guid}},client:structuredClone(baseline.assets.client),scripts:[]}};
save.assets.client.root.children=[];
console.log('exporting',data.images.length);
const result=exportGia(save.assets.server,{scripts:[]});
const validation=validateServerGiaCompatibility(result.buffer);
assert(validation.valid,JSON.stringify(validation));
fs.writeFileSync(out+'/草神_18色矢量几何实验.gia',result.buffer);
console.log('reimporting',result.buffer.length);
const actual=importGia(result.buffer,'草神_18色矢量几何实验.gia');
save.assets.server=actual.project;save.assets.scripts=actual.scripts;
const actualHost=actual.project.root.children[0].children.find(n=>n.name===host.name);
assert.equal(actualHost.children.length,data.images.length);
assert(actualHost.children.every(n=>n.imageId===100003&&n.enableFill&&n.fillAmount===.5&&n.fillType==='Horizontal'&&n.fillHorizontalType==='Left'));
fs.writeFileSync(out+'/reimported.simulator.save.json',JSON.stringify(save));
console.log('starting simulator');
const studio=createStudio(save);studio.playStart({canvasId:'pc-16-9'});studio.playStep(1/60,{observe:false});
const state=studio.playGet({view:true,paint:true});
const errors=state.logs.filter(l=>['error','lua-error'].includes(l.level));assert.equal(errors.length,0,JSON.stringify(errors));
assert.equal(state.scene.nodes.filter(n=>n.kind==='image'&&n.imageId===100003).length,data.images.length);
console.log('rendering',state.canvasWidth,state.canvasHeight);
const png=renderPaintPng(state.paint,state.canvasWidth,state.canvasHeight).data;
fs.writeFileSync(out+'/actual-gia-simulator.png',png);studio.playStop();
const verification={...report,triangleSeamExpansionHDpixels:{width:1.2,height:.6},nativeGeometryImageCount:data.images.length,totalControls:guid-1076000000,giaBytes:result.buffer.length,giaStructuralValidation:true,actualGiaReimported:true,halfTriangleFillPreserved:true,simulatorRuntimeErrors:errors.length,simulatorRendered:true,pngReplacement:false,deviceVerified:false,warnings:result.warnings||[]};
fs.writeFileSync(out+'/verification.json',JSON.stringify(verification,null,2));
console.log(JSON.stringify({giaBytes:result.buffer.length,nativeTriangleImages:data.images.length,errors:errors.length,png:out+'/actual-gia-simulator.png'}));
