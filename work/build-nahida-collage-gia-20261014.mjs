import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {createNode} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/ui/authoring.js';
import {exportGia,importGia,validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
import {renderPaintPng} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';
const out=process.env.COLLAGE_OUTPUT||'outputs/nahida-native-collage-20261014';
const data=JSON.parse(fs.readFileSync(out+'/collage.json'));
const giaName=`草神_${data.elements.length}基础图元拼装.gia`;
const report=JSON.parse(fs.readFileSync(out+'/report.json'));
const base=JSON.parse(fs.readFileSync('outputs/full-reinstall/simulator.save.json'));
let guid=1076200000;
function node(kind,name,props={}){return createNode(kind,{name,id:'nc'+guid,guid:guid++,syncAllDevices:false,...props});}
function place(n,x,y,w,h,z=0,scale=1){for(const t of Object.values(n.transformByPlatform)){t.anchorMin={x:.5,y:.5};t.anchorMax={x:.5,y:.5};t.pivot={x:.5,y:.5};t.offset={x,y};t.size={x:w,y:h};t.scale={x:scale,y:scale,z:1};t.rotation={x:0,y:0,z};}return n;}
const root=node('server-container','草神基础图元拼装小样');
const stage=place(node('container','CollageStudyStage'),0,0,1600,900);
root.children=[stage];
stage.children.push(place(node('image','背景',{imageId:100001,imageColor:0xfff5f3ed}),0,0,1600,900));
const host=place(node('container','草神拼装'),0,-25,data.w,data.h,0,1.4);stage.children.push(host);
const ids={rectangle:100001,ellipse:100002,triangle:100003,fourstar:100004};
let group=null,lastPart=null,groups=0;
for(const [index,e] of data.elements.entries()){
 if(e.part!==lastPart){group=place(node('container',e.part+'-'+(++groups)),0,0,data.w,data.h);host.children.push(group);lastPart=e.part;}
 const n=node('image',e.part+' / '+e.name+' #'+index,{imageId:ids[e.type],imageColor:(0xff000000|parseInt(e.color.slice(1),16))>>>0});
 place(n,e.x-data.w/2,data.h/2-e.y,e.width,e.height,e.rotation);group.children.push(n);
}
// Static candidates can retain semantic part labels on images without a
// redundant container for every interleaved detail layer.
if(process.env.COLLAGE_FLAT_GROUPS==='1'){host.children=host.children.flatMap(g=>g.children);groups=0;}
function label(name,text,y,size=23){const n=node('textbox',name,{text,fontSize:size,minimumFontSize:size,fontColor:0xff354139,bgColor:0,enableOutline:false,horizontalAlignment:'Middle',verticalAlignment:'Middle'});stage.children.push(place(n,0,y,1500,40));}
label('Title','草神 · 基础图元拼装 · 实际 GIA 回读模拟器',382,27);
label('Count',`${data.elements.length} 个角色图片图元 · 按发束、五官、衣片和身体部件拼装`,340,21);
label('Note','第一版造型小样；轮廓与细节仍有差异，真机未验证。',-390,19);
stage.children.reverse();host.children.reverse();for(const g of host.children)g.children.reverse();
const save={format:base.format,version:base.version,meta:{name:root.name},activeAssetType:base.activeAssetType,serverLogic:{version:1,rules:[]},assets:{server:{...base.assets.server,root,meta:{...base.assets.server.meta,name:root.name,sourceFile:'',giaFileName:giaName,giaFileId:root.guid}},client:structuredClone(base.assets.client),scripts:[]}};
save.assets.client.root.children=[];
const result=exportGia(save.assets.server,{scripts:[]});assert(validateServerGiaCompatibility(result.buffer).valid);
fs.writeFileSync(out+'/'+giaName,result.buffer);
const actual=importGia(result.buffer,giaName);save.assets.server=actual.project;save.assets.scripts=actual.scripts;
const all=[];function walk(n){all.push(n);for(const c of n.children||[])walk(c);}walk(actual.project.root);
const primitives=all.filter(n=>n.kind==='image'&&n.name!=='背景');assert.equal(primitives.length,data.elements.length);
const expected=new Map(data.elements.map((e,i)=>[e.part+' / '+e.name+' #'+i,e]));
for(const n of primitives){const e=expected.get(n.name);assert(e);assert.equal(n.imageId,ids[e.type]);assert.equal(n.imageColor,(0xff000000|parseInt(e.color.slice(1),16))>>>0);for(const t of Object.values(n.transformByPlatform)){assert(Math.abs(t.size.x-e.width)<.001);assert(Math.abs(t.size.y-e.height)<.001);assert(Math.abs(t.rotation.z-e.rotation)<.001);}}
fs.writeFileSync(out+'/reimported.simulator.save.json',JSON.stringify(save));
const studio=createStudio(save);studio.playStart({canvasId:'pc-16-9'});studio.playStep(1/60,{observe:false});
const state=studio.playGet({view:true,paint:true});assert.equal(state.logs.filter(l=>['error','lua-error'].includes(l.level)).length,0);
fs.writeFileSync(out+'/actual-gia-simulator.png',renderPaintPng(state.paint,state.canvasWidth,state.canvasHeight).data);studio.playStop();
const verification={...report,partLayerContainers:groups,totalControls:all.length,giaBytes:result.buffer.length,giaStructuralValidation:true,actualGiaReimported:true,primitiveTransformsAndColorsPreserved:true,simulatorRuntimeErrors:0,pngReplacement:false,gameIntegrated:false,deviceVerified:false};
fs.writeFileSync(out+'/verification.json',JSON.stringify(verification,null,2));console.log(JSON.stringify(verification));
