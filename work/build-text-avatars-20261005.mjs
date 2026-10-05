import fs from 'node:fs';import assert from 'node:assert/strict';
import {decompress,expandCompact} from './v2-pack.mjs';
import {exportGia,validateServerGiaCompatibility,importGia} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const out=process.env.TEXT_AVATAR_OUT||'outputs/text-avatars-20261005';fs.mkdirSync(out,{recursive:true});
const save=JSON.parse(fs.readFileSync('outputs/loading-fix-20261005/simulator.save.json'));let lua=save.assets.scripts[0].source;
const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean);
const host=find(save.assets.server.root,'FighterDemo');const proto=find(host,'LoadingText');let guid=1073910000;
function textNode(parent){const n=structuredClone(proto);n.id='avatar_text_'+guid;n.guid=guid++;n.name='TextArt';n.text='';n.visible=true;n.active=true;n.children=[];n.fontSize=12;n.minimumFontSize=12;n.adaptiveFontSize=false;n.enableOutline=false;n.fontColor=0xffffffff;n.bgColor=0;n.horizontalAlignment='Left';n.verticalAlignment='Top';n.raycastTarget=false;delete n.giaRaw.textAlign;delete n.giaRaw.textVerticalAlign;delete n.giaRelatedGuids;delete n.giaInfoIndex;delete n.scriptMappingIds;for(const t of Object.values(n.transformByPlatform)){t.anchorMin={x:.5,y:.5};t.anchorMax={x:.5,y:.5};t.pivot={x:.5,y:.5};t.offset={x:0,y:0};t.size={x:2000,y:1700};t.scale={x:1,y:1,z:1};}parent.children.unshift(n);}
const jobsLine=lua.split('\n').find(s=>s.startsWith('local loadingJobs='));const jobs=[...jobsLine.matchAll(/\{path=\{([^}]*)\},prefix="([^"]*)",count=(\d+)\}/g)].map(m=>({path:JSON.parse('['+m[1]+']'),prefix:m[2],count:Number(m[3])}));
const converted=jobs.filter(j=>['HomePx','FacePx','IconPx'].includes(j.prefix));assert.equal(converted.length,14);
for(const job of converted){let parent=host;for(const name of job.path)parent=parent.children.find(n=>n.name===name);assert(parent);textNode(parent);}
const kept=jobs.filter(j=>!converted.includes(j));lua=lua.replace(jobsLine,'local loadingJobs={'+kept.map(j=>'{path={'+j.path.map(JSON.stringify).join(',')+'},prefix='+JSON.stringify(j.prefix)+',count='+j.count+'}').join(',')+'}');
const reports=[];
function frameText(frame,key){
 const raw=expandCompact(decompress(Buffer.from(frame.data,'base64')));assert.equal(raw.length,frame.count*5);
 let w=Math.round(frame.anchor[0]*2),h=Math.round(frame.anchor[1]*2);
 for(let i=0;i<raw.length;i+=5){w=Math.max(w,raw[i]+raw[i+2]);h=Math.max(h,raw[i+1]+raw[i+3]);}
 const pixels=new Uint32Array(w*h);for(let i=0;i<raw.length;i+=5){const [x,y,rw,rh,p]=raw.subarray(i,i+5);for(let yy=y;yy<y+rh;yy++)for(let xx=x;xx<x+rw;xx++)pixels[yy*w+xx]=frame.palette[p-1];}
 const rows=[];let runs=0,visible=0;
 for(let y=0;y<h;y++){let row='';for(let x=0;x<w;){const color=pixels[y*w+x],begin=x;while(x<w&&pixels[y*w+x]===color)x++;if(color>>>24)visible+=x-begin;const rgb=(color&0xffffff).toString(16).padStart(6,'0'),alpha=(color>>>24).toString(16).padStart(2,'0');row+='<color=#'+rgb+alpha+'>'+'█'.repeat(x-begin)+'</color>';runs++;}rows.push(row);}
 const text='<b>'+rows.join('\n')+'</b>';reports.push({key,w,h,pixelCharacters:w*h,visiblePixels:visible,colorRuns:runs,richTextCodeUnits:text.length,utf8Bytes:Buffer.byteLength(text),oldImagePool:frame.count});
 const quote=JSON.stringify(text).replace(/[^\x00-\x7f]/gu,c=>Array.from(Buffer.from(c)).map(v=>'\\'+String(v).padStart(3,'0')).join(''));
 return '{textArt='+quote+',w='+w+',h='+h+',scale='+frame.scale+',anchor={'+frame.anchor+'}}';
}
function convertLine(prefix,label){const line=lua.split('\n').find(s=>s.startsWith(prefix));assert(line);const frames=[...line.matchAll(/\{scale=([^,]+),anchor=\{([^}]*)\},palette=\{([^}]*)\},data='([^']*)',count=(\d+),tokens=(\d+)\}/g)].map(m=>({scale:Number(m[1]),anchor:m[2].split(',').map(Number),palette:m[3].split(',').map(Number),data:m[4],count:Number(m[5])}));assert(frames.length);lua=lua.replace(line,prefix+'{'+frames.map((f,i)=>frameText(f,label+(i+1))).join(',')+'}');return frames.length;}
assert.equal(convertLine('local portraitData=','portrait-'),19);assert.equal(convertLine('local thumbData=','thumb-'),19);assert.equal(convertLine('resourceGate.homePortraitData=','home-'),2);
function rep(a,b){assert(lua.includes(a),'Missing '+a.slice(0,90));lua=lua.replace(a,()=>b);}
rep('local function paintFrame(parent,prefix,data,scale,nodes)',`resourceGate.textArtCache={}
-- Geometry calibration is a candidate for the native font: keep glyphs, including transparent cells,
-- identical so color does not change advances. Wide boxes prevent accidental word wrapping.
resourceGate.textArtAdvance=8.5
resourceGate.paintTextArt=function(parent,data,scale)
 local key=parent.name;local c=resourceGate.textArtCache[key]
 if not c then c={node=parent:FindChild('TextArt')};resourceGate.textArtCache[key]=c end
 local node=c.node;if not node then error('Missing TextArt '..key)end
 if c.frame~=data then
  local began=resourceGate.loader.clock and resourceGate.loader.clock()
  node.text=data.textArt;c.frame=data
  local ended=resourceGate.loader.clock and resourceGate.loader.clock()
  print('[TEXT APPLY] '..key..' bytes='..#data.textArt..' lua='..((began and ended)and ended-began or -1))
 end
 if c.scale~=scale then
  local advance=resourceGate.textArtAdvance;local line=14.4;local width=data.w*24+8;local height=data.h*line+24
  node:SetSizeDelta(width,height);node:SetLocalScale(scale/advance,scale/line,1)
  node:SetAnchoredPosition((width/2-2-data.anchor[1]*advance)*scale/advance,(data.anchor[2]*line-height/2)*scale/line)
  c.scale=scale
 end
end
local function paintFrame(parent,prefix,data,scale,nodes)
 if data and data.textArt then resourceGate.paintTextArt(parent,data,scale);return end`);
rep('local function want(frame)if frame then desired[frame]=true end end','local function want(frame)if frame and not frame.textArt then desired[frame]=true end end');
rep('local function visit(frame)\n  if seen[frame]then return end;', 'local function visit(frame)\n  if frame.textArt then return end\n  if seen[frame]then return end;');
lua=lua.replaceAll('GF10-FULL','GF10-TEXT-AVATAR');
save.assets.scripts[0].source=lua;save.assets.scripts[0].path='lua/gpt_20261005_头像文本对照_完整游戏.lua';save.assets.scripts[0].filename='gpt_20261005_头像文本对照_完整游戏.lua';save.meta.name='头像全部文本加载对照';save.assets.server.root.name='gpt_20261005_头像文本对照_A';save.assets.server.meta.name=save.assets.server.root.name;save.assets.server.meta.giaFileName='gpt_20261005_头像文本对照_A.gia';
fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(save));fs.writeFileSync(out+'/完整游戏.lua',lua);
const native=JSON.parse(fs.readFileSync('outputs/loading-fix-20261005/fighter.save.json'));native.assets.server=structuredClone(save.assets.server);native.assets.scripts=structuredClone(save.assets.scripts);native.meta=structuredClone(save.meta);fs.writeFileSync(out+'/fighter.save.json',JSON.stringify(native));
const a=exportGia(native.assets.server,{scripts:native.assets.scripts});assert(validateServerGiaCompatibility(a.buffer).valid);assert(importGia(a.buffer,'头像全部文本对照_A.gia').scripts.some(s=>s.source===lua));fs.writeFileSync(out+'/头像全部文本对照_A.gia',a.buffer);
const report={base:'loading-fix-20261005',addedTextControls:14,removedImageJobPools:converted,homeAvoidedImageCreates:converted.filter(j=>j.prefix==='HomePx').reduce((sum,j)=>sum+j.count,0),frames:reports,gameActorPoolsUnchanged:true,stagePoolsUnchanged:true,sourceGridPreserved:true,richTextTags:['b','color #RRGGBBAA'],transparentCells:'same block glyph with alpha zero; no blank layers',nativeFontCalibrationVerified:false,nativeRichTextVerified:false,simulatorRichTextSupported:false,deviceVerified:false,aBytes:a.buffer.length};fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2));console.log(JSON.stringify({out,homeAvoidedImageCreates:report.homeAvoidedImageCreates,textControls:14,aBytes:a.buffer.length,home:reports.filter(r=>r.key.startsWith('home'))}));
fs.writeFileSync(out+'/gpt_20261005_头像文本对照_A.gia',a.buffer);fs.writeFileSync(out+'/gpt_20261005_头像文本对照_完整游戏.lua',lua);
const baseDelivery=JSON.parse(fs.readFileSync('outputs/full-reinstall/delivery.json'));const b=baseDelivery.files.find(f=>f.filename.includes('_B_'));fs.copyFileSync('outputs/full-reinstall/'+b.filename,out+'/gpt_20261005_头像文本对照_B.gia');
