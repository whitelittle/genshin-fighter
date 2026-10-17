import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {validateServerGiaCompatibility,importGia} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const out=process.env.DUEL_LOAD_OUT||'outputs/duel-loading';mkdirSync(out,{recursive:true});
const save=JSON.parse(readFileSync(process.env.DUEL_LOAD_INPUT||'outputs/duel-vnext/fighter.save.json'));
const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean);
const host=find(save.assets.server.root,'FighterDemo');
const group=structuredClone(find(host,'Art')),image=structuredClone(find(host,'Hp1')),text=structuredClone(find(host,'Status'));
let serial=0;
function make(proto,name,parent,x,y,w,h){const n=structuredClone(proto);n.id='loading_'+(++serial);n.name=name;n.children=[];n.active=true;n.visible=true;n.raycastTarget=false;delete n.scriptMappingIds;delete n.giaRelatedGuids;delete n.giaInfoIndex;for(const t of Object.values(n.transformByPlatform)){t.offset={x,y};t.size={x:w,y:h};t.scale={x:1,y:1,z:1};t.rotation={x:0,y:0,z:0};t.anchorMin=t.anchorMax=t.pivot={x:.5,y:.5};}parent.children.unshift(n);return n;}
const jobs=save._pixelJobs||[];
function collect(parent,path=[]){
 const pool=parent.name==='Sprite'||parent.name==='Phoenix'||parent.name==='BackdropArt'||/^Portrait[12]$/.test(parent.name)||/^Choose(Keqing|Diluc)Face$/.test(parent.name);
 const removed=[];
 for(const child of parent.children||[]){
  if(pool&&child.kind==='image'&&!child.name.startsWith('FaceFrame')){const t=child.transformByPlatform.KEYBOARD;removed.push([child.name,t.offset.x,t.offset.y,t.size.x,t.size.y,child.imageColor>>>0,child.visible!==false?1:0]);}
  else collect(child,[...path,child.name]);
 }
 if(removed.length){removed.sort((a,b)=>Number(a[0].match(/\d+$/)?.[0]||0)-Number(b[0].match(/\d+$/)?.[0]||0));jobs.push({path,rows:removed});parent.children=parent.children.filter(n=>!removed.some(r=>r[0]===n.name));}
}
collect(host);
const seed=make(group,'LoadingPixelTemplate',save.assets.client.root,0,0,16,16);
const seedImage=make(image,'Pixel',seed,0,0,16,16);seedImage.imageColor=0xffffffff;
const reference=make(group,'LoadingPixelTemplate',host,0,0,1,1);reference.kind='reference';reference.visible=false;
const overlay=make(group,'LoadingScreen',host,0,0,1,1);
const black=make(image,'LoadingBlack',overlay,0,0,1600,1000);black.imageColor=0xff000000;
const track=make(image,'LoadingTrack',overlay,0,-285,760,8);track.imageColor=0xff26303c;
const bar=make(image,'LoadingBar',overlay,-380,-285,1,8);bar.imageColor=0xfff7e5ba;
const label=make(text,'LoadingText',overlay,0,-320,1180,56);label.fontSize=18;label.fontColor=0xffffffff;label.text='等待 Lua 启动：请检查脚本是否挂在 FighterDemo 容器上';
const mascot=make(group,'LoadingPaimon',overlay,-380,-245,1,1);
const paimon=JSON.parse(readFileSync('assets/vnext/paimon-loading.json'));
const mascotPool=Math.max(...paimon.map(f=>f.rows.length));
for(let i=1;i<=mascotPool;i++){const r=paimon[0].rows[i-1],f=paimon[0];const n=make(image,'M'+i,mascot,r?(r[0]+r[2]/2-f.anchor[0])*f.scale:0,r?(f.anchor[1]-r[1]-r[3]/2)*f.scale:0,r?r[2]*f.scale:1,r?r[3]*f.scale:1);n.visible=!!r;if(r)n.imageColor=((r[7]<<24)|(r[4]<<16)|(r[5]<<8)|r[6])>>>0;}
// Front-to-back ordering used by the existing UI exporter.
overlay.children=[mascot,label,bar,track,black];
const luaString=s=>JSON.stringify(s);
const luaFrame=f=>'{scale='+f.scale+',anchor={'+f.anchor.join(',')+'},rows={'+f.rows.map(r=>'{'+r.join(',')+'}').join(',')+'}}';
const data='local loadingJobs={'+jobs.map(j=>'{path={'+j.path.map(luaString).join(',')+'},prefix='+luaString(j.prefix)+',count='+j.count+'}').join(',')+'}\nlocal loadingPaimonFrames={'+paimon.map(luaFrame).join(',')+'}\n';
let source=save.assets.scripts[0].source;
for(const prefix of ['P','F','B','FacePx'])source=source.replaceAll("pool:FindChild('"+prefix+"'..n)","loadingFind(pool,'"+prefix+"'..n)");
source=readFileSync('work/duel-loading-prefix.lua','utf8')+'\n'+data+'\n'+source+'\n'+readFileSync(process.env.DUEL_LOAD_RUNTIME||'work/duel-loading-runtime.lua','utf8');
// Preserve device-compatible ASCII byte escapes, including the loading labels.
source=source.replace(/[^\x00-\x7f]/gu,c=>Array.from(Buffer.from(c)).map(v=>'\\'+String(v).padStart(3,'0')).join(''));
delete save._pixelJobs;save.assets.scripts[0].source=source;save.assets.scripts[0].path='lua/fighter_duel_loading_v2.lua';save.assets.scripts[0].filename='fighter_duel_loading_v2.lua';
save.assets.server.root.name='FighterDuelLoading';save.meta.name='原神格斗 · 双人黑屏分批加载';
let guid=1073741850,controls=0;function compact(n){n.guid=guid++;controls++;delete n.giaRelatedGuids;delete n.giaInfoIndex;delete n.scriptMappingIds;for(const c of n.children||[])compact(c);}compact(save.assets.server.root);if(save.assets.client?.root)compact(save.assets.client.root);
reference.referencedPrefabId=seed.guid;
save.assets.scripts[0].guid=guid++;save.assets.scripts[0].id=String(save.assets.scripts[0].guid);
save.assets.server.meta.name='FighterDuelLoading';save.assets.server.meta.giaFileName='原神格斗_双人黑屏加载.gia';save.assets.server.meta.giaFileId=save.assets.server.root.guid;
writeFileSync(out+'/fighter.save.json',JSON.stringify(save));writeFileSync(out+'/fighter_duel_loading_v2.lua',source);
const ex=createStudio(save).exportData('gia-combined'),buffer=Buffer.from(ex.data,ex.encoding),v=validateServerGiaCompatibility(buffer);assert.ok(v.valid,JSON.stringify(v));assert.ok(importGia(buffer,'原神格斗_双人黑屏加载.gia').scripts.some(s=>s.path==='lua/fighter_duel_loading_v2.lua'));
writeFileSync(out+'/原神格斗_双人黑屏加载.gia',buffer);
writeFileSync(out+'/build.json',JSON.stringify({staticControls:controls,deferredImages:jobs.reduce((a,j)=>a+(j.count||j.rows?.length||0),0),mascotPool,giaBytes:buffer.length,deviceVerified:false},null,2));
console.log(readFileSync(out+'/build.json','utf8'));
