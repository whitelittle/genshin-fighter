import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createStudio,validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {renderPaintPng} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';
const out='outputs/text-scene-probe-20261005';fs.mkdirSync(out,{recursive:true});
const baseline=JSON.parse(fs.readFileSync('outputs/full-reinstall/simulator.save.json'));
const data=JSON.parse(fs.readFileSync('outputs/scene-candidate-1-fit-20261005/224x126-16colors.json'));
function find(n,p){if(p(n))return n;for(const c of n.children||[]){const hit=find(c,p);if(hit)return hit;}}
const textProto=find(baseline.assets.server.root,n=>n.kind==='textbox');
const root=structuredClone(baseline.assets.server.root);root.name='TextSceneProbe';root.children=[];
const host=structuredClone(baseline.assets.server.root.children[0]);host.name='TextProbe';host.children=[];root.children=[host];
let id=0,guid=1073800000;root.guid=guid++;host.guid=guid++;
function text(name,value,x,y,w,h,font=18,color=0xffffffff,sx=1,sy=1){
 const n=structuredClone(textProto);n.id='txtprobe_'+(++id);n.guid=guid++;n.name=name;n.text=value;n.children=[];n.fontSize=font;n.minimumFontSize=font;n.adaptiveFontSize=false;n.fontColor=color;n.bgColor=0;n.enableOutline=false;n.horizontalAlignment='Left';n.verticalAlignment='Top';n.raycastTarget=false;n.syncAllDevices=false;
 delete n.scriptMappingIds;delete n.giaRelatedGuids;delete n.giaInfoIndex;
 for(const t of Object.values(n.transformByPlatform)){t.anchorMin={x:.5,y:.5};t.anchorMax={x:.5,y:.5};t.pivot={x:.5,y:.5};t.offset={x,y};t.size={x:w,y:h};t.scale={x:sx,y:sy,z:1};t.rotation={x:0,y:0,z:0};}
 host.children.push(n);return n;
}
// At font 12 in the host font, block advance=8.5; these three blanks total 4+3+1.5.
// Browser font fallback remains a measured condition, not an assumed engine guarantee.
const glyph='█',blank='\u2004\u2005\u200a',font=12,advance=8.5,line=14.4;
const colors=[...new Set(data.rows.map(r=>((r[7]<<24)|(r[4]<<16)|(r[5]<<8)|r[6])>>>0))];assert.equal(colors.length,16);
const pixels=new Uint32Array(data.w*data.h);for(const [x,y,w,h,r,g,b,a] of data.rows){const color=((a<<24)|(r<<16)|(g<<8)|b)>>>0;for(let py=y;py<y+h;py++)for(let px=x;px<x+w;px++)pixels[py*data.w+px]=color;}
const width=data.w*advance+8,height=data.h*line+4,sx=1120/width,sy=630/height;
let chars=0,bytes=0;
for(let k=0;k<colors.length;k++){
 const rows=[];for(let y=0;y<data.h;y++){let s='';for(let x=0;x<data.w;x++)s+=pixels[y*data.w+x]===colors[k]?glyph:blank;rows.push(s);}
 const value=rows.join('\n');chars+=value.length;bytes+=Buffer.byteLength(value);
 text('ColorLayer'+(k+1),value,0,-5,width,height,font,colors[k],sx,sy);
}
text('Title','文字场景探针 · 16 色 / 224×126 / 16 个场景文字控件',0,375,1400,42,26);
text('Hint','静态显示，无角色动画。检查色层对齐、字块缝隙；手机负载尚未验证。',0,335,1400,34,18);
text('Calibration','对齐检查：下面两行最后的 | 应处于同一列',0,-350,1400,24,16);
text('Filled','|'+glyph.repeat(32)+'|',-440,-380,400,22,12,0xfff9d86a);
text('Blank','|'+blank.repeat(32)+'|',-440,-405,400,22,12,0xff72dbed);
text('Counts',`场景：16 文本层 / ${data.rows.length} 矩形对照 / ${chars.toLocaleString('en-US')} 字符（含空白）`,140,-390,640,40,15);
const save={format:baseline.format,version:baseline.version,meta:{name:'文字场景独立探针'},activeAssetType:baseline.activeAssetType,serverLogic:{version:1,rules:[]},assets:{server:{...baseline.assets.server,root,meta:{...baseline.assets.server.meta,name:'TextSceneProbe',sourceFile:'',giaFileName:'文字场景探针.gia',giaFileId:root.guid}},client:structuredClone(baseline.assets.client),scripts:[]}};
save.assets.client.root.children=[];save.assets.client.meta.sourceFile='';
fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(save));
const studio=createStudio(save);studio.playStart();studio.playStep(1/60);const state=studio.playGet({view:true,paint:true});assert.equal(state.logs.filter(l=>['error','lua-error'].includes(l.level)).length,0);assert.equal(state.scene.nodes.filter(n=>/^ColorLayer/.test(n.name)).length,16);
fs.writeFileSync(out+'/host-preview.png',renderPaintPng(state.paint,state.canvasWidth,state.canvasHeight).data);studio.playStop();
const exported=createStudio(save).exportData('gia-combined');const buffer=Buffer.from(exported.data,exported.encoding);const validation=validateServerGiaCompatibility(buffer);assert.ok(validation.valid,JSON.stringify(validation));fs.writeFileSync(out+'/文字场景探针.gia',buffer);
const report={sceneTextControls:16,totalTextControls:id,totalServerControls:id+2,rectangleComparison:data.rows.length,charactersIncludingWhitespace:chars,utf8TextBytes:bytes,grid:[data.w,data.h],glyph,blankCodepoints:['U+2004','U+2005','U+200A'],fontSize:font,hostAdvance:advance,estimatedFullLayerRgbaMiB:width*height*4*16/1048576,giaBytes:buffer.length,staticOnly:true,simulatorStructuralCheck:true,browserVisualVerified:false,deviceVerified:false};fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2));
fs.writeFileSync(out+'/说明.md','# 文字场景独立探针\n\n设计：将16色场景按颜色拆为16个文字控件，以实心方块和空白字符排列。保留原始素材和210009。没有持续换帧或Lua更新。\n\n程序：网格224×126；场景16个文本层，附标题及对齐检查。空白组合依赖字体度量，平台字体变化可能错位。文字总长度、GIA大小、整层文字纹理估算见report.json。\n\n模拟器：结构检查通过、无Lua错误；host-preview.png为离屏渲染。浏览器实际效果另行确认。整层文字纹理可能较大，控件减少不能直接推断省电。\n\n真机：未验证。字数限制、字体、排版、手机发热与耗电、动态换帧成本仍待测。\n');console.log(JSON.stringify(report));
