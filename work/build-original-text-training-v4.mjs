import fs from 'node:fs';import assert from 'node:assert/strict';import {createRequire} from 'node:module';import crypto from 'node:crypto';
import {exportGia,validateServerGiaCompatibility,importGia} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const req=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json');const {createCanvas,loadImage}=req('@napi-rs/canvas');
const out='outputs/original-text-training-v4-20261005';fs.mkdirSync(out,{recursive:true});fs.mkdirSync(out+'/rasters',{recursive:true});
const save=JSON.parse(fs.readFileSync('outputs/text-avatars-chunk-v3-20261005/simulator.save.json'));let lua=save.assets.scripts[0].source;
const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean);
const quote=s=>JSON.stringify(s).replace(/[^\x00-\x7f]/gu,c=>Array.from(Buffer.from(c)).map(v=>'\\'+String(v).padStart(3,'0')).join(''));
const decode=s=>Buffer.from(JSON.parse('"'+s.replace(/\\(\d{3})/g,(_,v)=>'\\u00'+Number(v).toString(16).padStart(2,'0'))+'"'),'latin1').toString('utf8');
const replace=(a,b)=>{assert(lua.includes(a),'Missing '+a.slice(0,100));lua=lua.replace(a,()=>b);};
const reports=[],groups={home:[],portrait:[],thumb:[],stage:[]};
async function raster(path,w,h,crop,contain=false,quantStep=1){
 const im=await loadImage(path),c=createCanvas(w,h),ctx=c.getContext('2d');ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';
 const [sx,sy,sw,sh]=crop||[0,0,im.width,im.height];let dw=w,dh=h,dx=0,dy=0;
 if(contain){const s=Math.min((w-2)/sw,(h-2)/sh);dw=Math.round(sw*s);dh=Math.round(sh*s);dx=Math.floor((w-dw)/2);dy=Math.floor((h-dh)/2);}
 ctx.drawImage(im,sx,sy,sw,sh,dx,dy,dw,dh);const data=ctx.getImageData(0,0,w,h);
 for(let i=0;i<data.data.length;i+=4){if(data.data[i+3]<8){data.data[i]=data.data[i+1]=data.data[i+2]=data.data[i+3]=0;}else if(quantStep>1)for(let k=0;k<3;k++)data.data[i+k]=Math.min(255,Math.round(data.data[i+k]/quantStep)*quantStep);}
 return {c,ctx,data,path,source:[im.width,im.height],w,h,quantStep};
}
function frame(r,family,key,scale){
 const {w,h}=r,pixels=[];for(let i=0;i<r.data.data.length;i+=4)pixels.push(Buffer.from(r.data.data.subarray(i,i+4)).toString('hex').toUpperCase());
 const chunks=[],covered=new Uint8Array(w*h);let glyphs=0;
 const encode=colors=>{let t='<b>';for(let i=0;i<colors.length;){let j=i+1;while(j<colors.length&&colors[j]===colors[i])j++;t+='<color=#'+colors[i]+'>'+'█'.repeat(j-i)+'</color>';i=j;}return t+'</b>';};
 // One explicit-positioned text row avoids native newline leading entirely.
 // Adjacent fragments share one source pixel, so guard pixels use the original color.
 for(let y=0;y<h;y++){let x=0;while(x<w){while(x<w&&pixels[y*w+x].endsWith('00'))x++;if(x>=w)break;const start=x,colors=[];let text='';
  while(x<w&&colors.length<256){const next=[...colors,pixels[y*w+x]],candidate=encode(next);if(Buffer.byteLength(candidate)>1000)break;colors.push(pixels[y*w+x]);text=candidate;x++;}
  assert(x>start);let count=colors.length;while(count>1&&colors[count-1].endsWith('00'))count--;if(count!==colors.length)text=encode(colors.slice(0,count));
  chunks.push({x:start,y,w:count,h:1,text});glyphs+=count;for(let k=0;k<count;k++)covered[y*w+start+k]=1;
  if(x<w&&!pixels[y*w+x-1].endsWith('00')&&count>1)x--;
 }}
 for(let i=0;i<pixels.length;i++)if(!pixels[i].endsWith('00'))assert(covered[i],'Uncovered source pixel '+key+':'+i);
 // Identical fragments on consecutive rows can share one stretched glyph row, exactly.
 // This removes duplicate controls without altering any sampled color or pixel position.
 const merged=[],last=new Map();for(const chunk of chunks){const k=chunk.x+':'+chunk.w+':'+chunk.text;const prior=last.get(k);if(prior&&prior.y+prior.h===chunk.y)prior.h++;else{last.set(k,chunk);merged.push(chunk);}}
 r.ctx.putImageData(r.data,0,0);fs.writeFileSync(out+'/rasters/'+key+'.png',r.c.toBuffer('image/png'));
 const report={family,key,source:r.path,sourceSize:r.source,grid:[w,h],rgbQuantStep:r.quantStep,sourceGridSha256:crypto.createHash('sha256').update(r.data.data).digest('hex'),chunks:merged.length,unmergedRowChunks:chunks.length,glyphs,maxChunkUtf8Bytes:Math.max(...merged.map(c=>Buffer.byteLength(c.text))),sourceGridCoverage:true,sampledDirectlyFromPng:true};reports.push(report);groups[family].push(merged.length);
 const palette=[],index=new Map();const encoded=merged.map(c=>{let runs='';for(const m of c.text.matchAll(/<color=#([A-F0-9]{8})>(█+)<\/color>/g)){if(!index.has(m[1])){palette.push(m[1]);index.set(m[1],palette.length);}runs+=index.get(m[1]).toString(16).padStart(6,'0')+m[2].length.toString(16).padStart(3,'0');}return '{x='+c.x+',y='+c.y+',w='+c.w+',h='+c.h+',runs="'+runs+'"}';});
 return '{textArt=true,palette={'+palette.map(quote).join(',')+'},chunks={'+encoded.join(',')+'},w='+w+',h='+h+',scale='+scale+',anchor={'+w/2+','+h/2+'}}';
}
const homeImage=await loadImage('outputs/group1-full-test/home-halfbody-v2.png'),homeFrames=[];
for(let i=0;i<2;i++){
 const r=await raster('outputs/group1-full-test/home-halfbody-v2.png',256,256,[i*homeImage.width/2,0,homeImage.width/2,homeImage.height]);
 // Keep the earlier right-panel cleanup, excluding the neighboring left portrait's stray hair.
 if(i===1)for(let y=0;y<256;y++)for(let x=0;x<Math.ceil(12*256/112);x++)r.data.data.fill(0,(y*256+x)*4,(y*256+x+1)*4);
 homeFrames.push(frame(r,'home','home-'+(i?'diluc':'keqing'),600/256));
}
const roster=JSON.parse(fs.readFileSync('assets/roster-v2/roster.json'));const rolesLine=lua.split('\n').find(l=>l.startsWith('local roleNames='));
const names=[...rolesLine.matchAll(/"((?:\\.|[^"\\])*)"/g)].map(m=>decode(m[1]));assert.equal(names.length,19);
const portraits=[],thumbs=[];
for(const name of names){const entry=roster.find(r=>r[1]===name);assert(entry,'No source mapping '+name);const key=entry[0];const path=key==='lawachurl'?'assets/roster-v2/lawachurl-reference.webp':'assets/roster-v2/'+key+'-official-head.png';const crop=key==='lawachurl'?[65,8,370,340]:undefined;
 portraits.push(frame(await raster(path,96,96,crop,true),'portrait',key+'-portrait',120/96));
 thumbs.push(frame(await raster(path,64,64,crop,true),'thumb',key+'-thumb',70.4/64));
}
const stageFrame=frame(await raster('assets/training-room-20261005/training-room-paimon-source.png',1280,720,undefined,false,8),'stage','training-room',1);
for(const [prefix,frames]of [['resourceGate.homePortraitData=',homeFrames],['local portraitData=',portraits],['local thumbData=',thumbs]]){const line=lua.split('\n').find(l=>l.startsWith(prefix));assert(line);replace(line,prefix+'{'+frames.join(',')+'}');}
replace("paintFrame(pool,'FacePx',portraitData[role],menuMode=='battle'and 1.45 or 2.7,portraitNodes[i])","paintFrame(pool,'FacePx',portraitData[role],(menuMode=='battle'and 1.45 or 2.7)*48/portraitData[role].w,portraitNodes[i])");
replace("paintFrame(rootNode('GridFace'..n),'IconPx',thumbData[role],2.3,gridNodes[n])","paintFrame(rootNode('GridFace'..n),'IconPx',thumbData[role],2.3*32/thumbData[role].w,gridNodes[n])");
const collisionLine=lua.split('\n').find(l=>l.startsWith('local Collision='));assert(collisionLine);
replace(collisionLine,'local Collision={results={},profiles={},moves={},stageData={'+stageFrame+'},stageNames={'+quote('训练室 · 派蒙涂鸦')+'}}');
const idStart=lua.indexOf('function Collision.stageId(seed,number)'),idEnd=lua.indexOf('\nend',idStart);assert(idStart>0&&idEnd>idStart);lua=lua.slice(0,idStart)+'function Collision.stageId(seed,number) return 1 end'+lua.slice(idEnd+4);
const jobsLine=lua.split('\n').find(l=>l.startsWith('local loadingJobs='));replace(jobsLine,jobsLine.replace(/,?\{path=\{"CountryStage"\},prefix="StagePx",count=\d+\}/,''));
const stageRequest="if mode=='battle'then local frame=resourceGate.stageFrame();local cw,ch=game.GetUICanvasSize();resourceGate.loader.stagePaint={frame=frame,n=1,scale=math.max(cw/frame.w,ch/frame.h),key=Collision.stageId(stage,plannedRound)..':'..cw..':'..ch};Collision.stageNodes={};loadingTotal=loadingTotal+math.ceil(frame.count/32)end";
replace(stageRequest,"if mode=='battle'then local frame=resourceGate.stageFrame();local cw,ch=game.GetUICanvasSize();local scale=math.max(cw/frame.w,ch/frame.h);local c=resourceGate.textNodes(rootNode('CountryStage'));if c.frame~=frame or c.scale~=scale then resourceGate.loader.stagePaint={frame=frame,n=1,scale=scale,key='1:'..cw..':'..ch};Collision.stageNodes={};loadingTotal=loadingTotal+math.ceil(#frame.chunks/16)end end");
const paintStart=lua.indexOf("   if paint and paint.n<=paint.frame.count"),paintEnd=lua.indexOf('\n   if paint then',paintStart);assert(paintStart>0&&paintEnd>paintStart);
lua=lua.slice(0,paintStart)+`   if paint and paint.n<=#paint.frame.chunks then
    local parent=rootNode('CountryStage')
    for n=paint.n,math.min(#paint.frame.chunks,paint.n+15)do resourceGate.paintTextChunk(parent,paint.frame,paint.scale,n);resourceGate.loader.stats.painted=resourceGate.loader.stats.painted+1 end
    paint.n=paint.n+16;loadingDone=loadingDone+1;return true
   end`+lua.slice(paintEnd);
const begin=lua.indexOf('resourceGate.textArtCache={}'),end=lua.indexOf('local function paintFrame(',begin);assert(begin>0&&end>begin);
lua=lua.slice(0,begin)+`resourceGate.textArtCache={}
resourceGate.textGeometry={advance=20,glyphHeight=20,edgeFill=1.025,padX=2,padY=0}
resourceGate.textNodes=function(parent)
 local c=resourceGate.textArtCache[parent.name]
 if not c then c={nodes={}};for _,node in ipairs(parent:GetChildren())do local i=tonumber(string.match(node.name,'^TextArt(%d+)$'));if i then c.nodes[i]=node end end;resourceGate.textArtCache[parent.name]=c end
 return c
end
resourceGate.paintTextChunk=function(parent,data,scale,i)
 local c=resourceGate.textNodes(parent);local node=c.nodes[i];local chunk=data.chunks[i]
 if not node then error('Missing text row '..parent.name..':'..i)end
 if not chunk.text then
  local parts={'<b>'};for at=1,#chunk.runs,9 do local color=tonumber(string.sub(chunk.runs,at,at+5),16);local count=tonumber(string.sub(chunk.runs,at+6,at+8),16)
   parts[#parts+1]='<color=#'..data.palette[color]..'>'..string.rep('\\226\\150\\136',count)..'</color>'
  end;parts[#parts+1]='</b>';chunk.text=table.concat(parts)
  if #chunk.text>1000 then error('Rich text chunk budget exceeded')end
 end
 node.text=chunk.text;node:SetVisible(true)
 local g=resourceGate.textGeometry;local width,height=chunk.w*g.advance+40,60
 -- Native block glyph has no line-leading here. Source coordinates set every row independently.
 local fillHeight=chunk.h+(g.edgeFill-1)
 node:SetSizeDelta(width,height);node:SetLocalScale(scale/g.advance,scale/g.glyphHeight*fillHeight,1)
 node:SetAnchoredPosition((width/2-g.padX)*scale/g.advance+(chunk.x-data.anchor[1])*scale,(data.anchor[2]-chunk.y)*scale-height/2*scale/g.glyphHeight*fillHeight+g.padY*scale/g.glyphHeight)
end
resourceGate.paintTextArt=function(parent,data,scale)
 local c=resourceGate.textNodes(parent);if c.frame==data and c.scale==scale then return end
 for i,node in ipairs(c.nodes)do if data.chunks[i]then resourceGate.paintTextChunk(parent,data,scale,i)else node:SetVisible(false)end end
 c.frame=data;c.scale=scale
end
`+lua.slice(end);
// Mark loading's batched stage paint in the same cache, avoiding a synchronous repeat at handoff.
replace('if paint then Collision.stagePaintKey=paint.key end',"if paint then Collision.stagePaintKey=paint.key;local c=resourceGate.textNodes(rootNode('CountryStage'));c.frame=paint.frame;c.scale=paint.scale end");
lua=lua.replaceAll('GF10-TEXT-AVATAR-V3','GF10-ORIGINAL-TEXT-V4').replaceAll('TEXT-AVATAR-V3 /','ORIGINAL-TEXT-V4 /');
const host=find(save.assets.server.root,'FighterDemo'),proto=structuredClone(find(host,'TextArt1'));assert(proto);let guid=1077000000;const pools=[];
function setPool(n,count){n.children=(n.children||[]).filter(c=>!/^TextArt\d+$/.test(c.name));for(let i=1;i<=count;i++){const c=structuredClone(proto);c.name='TextArt'+i;c.id='original_text_'+guid;c.guid=guid++;c.children=[];c.text='';c.visible=false;c.fontSize=20;c.minimumFontSize=20;c.horizontalAlignment='Left';c.verticalAlignment='Top';delete c.giaRaw.textAlign;delete c.giaRaw.textVerticalAlign;n.children.push(c);}pools.push({parent:n.name,count});}
function walk(n){if((n.children||[]).some(c=>/^TextArt\d+$/.test(c.name))){const count=n.name==='HomeBust1'?groups.home[0]:n.name==='HomeBust2'?groups.home[1]:Math.max(...groups[n.name.startsWith('GridFace')?'thumb':'portrait']);setPool(n,count);}for(const c of n.children||[])if(!/^TextArt\d+$/.test(c.name))walk(c);}walk(host);setPool(find(host,'CountryStage'),groups.stage[0]);
save.assets.scripts[0].source=lua;save.assets.scripts[0].path='lua/gpt_20261005_原图文字训练室V4.lua';save.assets.scripts[0].filename='gpt_20261005_原图文字训练室V4.lua';
save.assets.server.root.name='gpt_20261005_原图文字训练室V4_尺寸修订_A';save.assets.server.meta.name=save.assets.server.root.name;save.assets.server.meta.giaFileName=save.assets.server.root.name+'.gia';save.meta.name='原图文字与派蒙训练室V4尺寸修订';
fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(save));fs.writeFileSync(out+'/完整游戏.lua',lua);
const native=JSON.parse(fs.readFileSync('outputs/text-avatars-chunk-v3-20261005/fighter.save.json'));native.assets.server=structuredClone(save.assets.server);native.assets.scripts=structuredClone(save.assets.scripts);fs.writeFileSync(out+'/fighter.save.json',JSON.stringify(native));
const exported=exportGia(native.assets.server,{scripts:native.assets.scripts});assert(validateServerGiaCompatibility(exported.buffer).valid);assert(importGia(exported.buffer,save.assets.server.meta.giaFileName).scripts.some(s=>s.source===lua));fs.writeFileSync(out+'/'+save.assets.server.meta.giaFileName,exported.buffer);
fs.writeFileSync(out+'/report.json',JSON.stringify({input:'original PNG, no fitted rectangle reconstruction',maxTextBytes:1000,singleRowFragments:true,guardPixels:1,edgeFill:1.025,trainingSceneSharedAcrossRounds:true,oldActorFxAndRulesPreserved:true,sceneRgbQuantizationMaxError:4,allFrames:reports,pools,totalTextControls:pools.reduce((s,p)=>s+p.count,0),aBytes:exported.buffer.length,nativeSeamsVerified:false,nativePerformanceVerified:false},null,2));
console.log(JSON.stringify({out,aBytes:exported.buffer.length,totalControls:pools.reduce((s,p)=>s+p.count,0),pools,stage:reports.at(-1)}));
