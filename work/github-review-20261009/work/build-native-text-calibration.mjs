import fs from 'node:fs';import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {exportGia,validateServerGiaCompatibility,importGia} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const out='outputs/native-text-calibration-20261005';fs.mkdirSync(out,{recursive:true});
const baseline=JSON.parse(fs.readFileSync('outputs/text-avatars-20261005/simulator.save.json'));
const find=(n,p)=>p(n)?n:(n.children||[]).map(c=>find(c,p)).find(Boolean);
const proto=find(baseline.assets.server.root,n=>n.kind==='textbox');
const root=structuredClone(baseline.assets.server.root);root.name='gpt_20261005_文字解析校准';const host=structuredClone(root.children[0]);host.children=[];host.name='TextCalibration';root.children=[host];
let guid=1073920000;root.guid=guid++;host.guid=guid++;
function text(name,value,x,y,w,h,font=20,kind='textbox'){
 const n=structuredClone(proto);n.id='cal_'+guid;n.guid=guid++;n.name=name;n.text=value;n.kind=kind;n.children=[];n.active=true;n.visible=true;n.raycastTarget=false;n.fontSize=font;n.minimumFontSize=font;n.adaptiveFontSize=false;n.fontColor=0xffffffff;n.bgColor=0;n.enableOutline=false;n.horizontalAlignment='Left';n.verticalAlignment='Top';delete n.giaRaw.textAlign;delete n.giaRaw.textVerticalAlign;delete n.giaInfoIndex;delete n.giaRelatedGuids;delete n.scriptMappingIds;
 if(kind==='textwindow'){n.showScrollBar=false;n.interactable=false;}
 for(const t of Object.values(n.transformByPlatform)){t.anchorMin={x:.5,y:.5};t.anchorMax={x:.5,y:.5};t.pivot={x:.5,y:.5};t.offset={x,y};t.size={x:w,y:h};t.scale={x:1,y:1,z:1};t.rotation={x:0,y:0,z:0};}host.children.push(n);return n;
}
text('Header','文字解析校准：左边预置内容，右边Lua赋值；独立包，不需要B或联机节点',0,415,1450,34,24);
text('Hint','彩色与加粗有效时不应看到标签原文。上下分别测试文本框和文本窗口。',0,375,1450,28,18);
const cases=[['纯文字 / 换行','████████\n████████'],['六位颜色 + 加粗','<b><color=#FF0000>████</color><color=#00FF00>████</color></b>'],['八位颜色 + 加粗','<b><color=#FF0000FF>████</color><color=#00FF00FF>████</color></b>'],['透明色与字格','<color=#FF0000FF>██</color><color=#00000000>██</color><color=#00FF00FF>██</color>\n██████']];
const assigns=[];let row=0;
for(const kind of ['textbox','textwindow'])for(const [label,value]of cases){const y=315-row*84;text('Label'+row,(kind==='textbox'?'文本框':'文本窗口')+'：'+label,0,y+22,1450,24,16);text('Static'+row,value,-360,y-18,680,66,20,kind);text('Dynamic'+row,'等待Lua赋值',360,y-18,680,66,20,kind);assigns.push(`script.object:FindChild('Dynamic${row}').text=${JSON.stringify(value).replace(/[^\x00-\x7f]/gu,c=>Array.from(Buffer.from(c)).map(v=>'\\'+String(v).padStart(3,'0')).join(''))}`);row++;}
const lua='function OnStart()\n'+assigns.join('\n')+'\nprint("TEXT-CALIBRATION-20261005 READY")\nend';
const save={format:baseline.format,version:baseline.version,meta:{name:'原生文字解析校准'},activeAssetType:baseline.activeAssetType,serverLogic:{version:1,rules:[]},assets:{server:{...baseline.assets.server,root,meta:{...baseline.assets.server.meta,name:root.name,giaFileName:root.name+'.gia',giaFileId:root.guid}},client:structuredClone(baseline.assets.client),scripts:[{...baseline.assets.scripts[0],id:String(guid),guid:guid++,controlId:host.id,path:'lua/native_text_calibration.lua',filename:'native_text_calibration.lua',source:lua}]}};
save.assets.client.root.children=[];fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(save));
const s=createStudio(save);s.playStart();const state=s.playGet({view:true});assert.equal(state.logs.filter(l=>['error','lua-error'].includes(l.level)).length,0);assert.equal(state.scene.nodes.filter(n=>n.name.startsWith('Dynamic')).length,8);s.playStop();
const result=exportGia(save.assets.server,{scripts:save.assets.scripts});assert(validateServerGiaCompatibility(result.buffer).valid);assert(importGia(result.buffer,root.name+'.gia').scripts.some(x=>x.source===lua));fs.writeFileSync(out+'/'+root.name+'.gia',result.buffer);
fs.writeFileSync(out+'/verification.json',JSON.stringify({structuralCheck:true,nativeVisualVerified:false,cases:cases.map(x=>x[0]),comparisons:['predefined vs Lua assignment','textbox vs textwindow'],independent:true,requiresPixelTemplate:false,requiresNetwork:false},null,2));
console.log('NATIVE_TEXT_CALIBRATION_PACKAGE_PASS');
