import fs from 'node:fs';import assert from 'node:assert/strict';
import {exportGia,validateServerGiaCompatibility,importGia} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const out='outputs/text-avatars-chunk-v3-20261005';fs.mkdirSync(out,{recursive:true});
const save=JSON.parse(fs.readFileSync('outputs/text-avatars-display-v2-20261005/simulator.save.json'));
let lua=save.assets.scripts[0].source;const reports=[];const families={home:[],portrait:[],thumb:[]};
const quote=s=>JSON.stringify(s).replace(/[^\x00-\x7f]/gu,c=>Array.from(Buffer.from(c)).map(v=>'\\'+String(v).padStart(3,'0')).join(''));
const decode=s=>Buffer.from(JSON.parse('"'+s.replace(/\\(\d{3})/g,(_,v)=>'\\u00'+Number(v).toString(16).padStart(2,'0'))+'"'),'latin1').toString('utf8');
for(const [prefix,family]of [['resourceGate.homePortraitData=','home'],['local portraitData=','portrait'],['local thumbData=','thumb']]){
 const line=lua.split('\n').find(l=>l.startsWith(prefix));assert(line);
 const converted=line.replace(/\{textArt="((?:\\.|[^"\\])*)",w=(\d+),h=(\d+),scale=([^,]+),anchor=\{([^}]*)\}\}/g,(_,encoded,ws,hs,scale,anchor)=>{
  const w=Number(ws),h=Number(hs),rows=decode(encoded).slice(3,-4).split('\n');assert.equal(rows.length,h);
  const grid=[];for(const row of rows){const colors=[];for(const m of row.matchAll(/<color=#([0-9a-fA-F]{8})>(█+)<\/color>/g))colors.push(...Array(m[2].length).fill(m[1].toUpperCase()));assert.equal(colors.length,w);grid.push(colors);}
  const chunks=[];const rebuilt=Array.from({length:h},()=>Array(w).fill('00000000'));
  const rowText=(y,x,tw)=>{let s='';for(let k=x;k<x+tw;){const color=grid[y][k],start=k;while(k<x+tw&&grid[y][k]===color)k++;s+='<color=#'+color+'>'+'█'.repeat(k-start)+'</color>';}return s;};
  for(let x=0;x<w;x+=16){const tw=Math.min(16,w-x);for(let y=0;y<h;){let parts=[],th=0;while(y+th<h&&th<8){const next=[...parts,rowText(y+th,x,tw)];if(Buffer.byteLength('<b>'+next.join('\n')+'</b>')>1000)break;parts=next;th++;}assert(th>0);const text='<b>'+parts.join('\n')+'</b>';
   if(grid.slice(y,y+th).some(row=>row.slice(x,x+tw).some(c=>!c.endsWith('00')))){
    chunks.push({x,y,w:tw,h:th,text});for(let yy=y;yy<y+th;yy++)for(let xx=x;xx<x+tw;xx++)rebuilt[yy][xx]=grid[yy][xx];
   }y+=th;
  }}
  // Omitted tiles contain only transparent cells; preserve all visible source pixels exactly.
  for(let y=0;y<h;y++)for(let x=0;x<w;x++)if(!grid[y][x].endsWith('00'))assert.equal(rebuilt[y][x],grid[y][x]);
  const report={family,index:families[family].length+1,w,h,chunks:chunks.length,maxUtf8Bytes:Math.max(...chunks.map(c=>Buffer.byteLength(c.text))),visiblePixelsPreserved:true};reports.push(report);families[family].push(chunks.length);
  return '{textArt=true,chunks={'+chunks.map(c=>'{x='+c.x+',y='+c.y+',w='+c.w+',h='+c.h+',text='+quote(c.text)+'}').join(',')+'},w='+w+',h='+h+',scale='+scale+',anchor={'+anchor+'}}';
 });assert.notEqual(converted,line);lua=lua.replace(line,()=>converted);
}
assert.equal(reports.length,40);
let guid=1073950000,totalControls=0;const pools=[];
function walk(n){const old=(n.children||[]).find(c=>c.name==='TextArt');if(old){let count;if(n.name==='HomeBust1')count=families.home[0];else if(n.name==='HomeBust2')count=families.home[1];else count=Math.max(...families[n.name.startsWith('GridFace')?'thumb':'portrait']);
 n.children=n.children.filter(c=>c!==old);for(let i=1;i<=count;i++){const c=structuredClone(old);c.name='TextArt'+i;c.id='text_chunk_'+guid;c.guid=guid++;c.text='';c.visible=false;c.fontSize=20;c.minimumFontSize=20;delete c.giaRaw.textAlign;delete c.giaRaw.textVerticalAlign;n.children.unshift(c);}totalControls+=count;pools.push({parent:n.name,controls:count});
 }for(const c of n.children||[])walk(c);}walk(save.assets.server.root);
const begin=lua.indexOf('resourceGate.textArtCache={}'),end=lua.indexOf('local function paintFrame(',begin);assert(begin>0&&end>begin);
lua=lua.slice(0,begin)+`resourceGate.textArtCache={}
-- Short rich-text chunks: native short parsing and scale passed; full portraits still need native QA.
resourceGate.paintTextArt=function(parent,data,scale)
 local key=parent.name;local c=resourceGate.textArtCache[key]
 if not c then c={nodes={}};for _,node in ipairs(parent:GetChildren())do
  local index=tonumber(string.match(node.name,'^TextArt(%d+)$'));if index then c.nodes[index]=node end
 end;resourceGate.textArtCache[key]=c end
 if c.frame==data and c.scale==scale then return end
 for i,node in ipairs(c.nodes)do
  local chunk=data.chunks[i];node:SetVisible(chunk~=nil)
  if chunk then
   if c.frame~=data then node.text=chunk.text end
   local advance,line=20,24;local width,height=chunk.w*advance+40,chunk.h*line+24
   node:SetSizeDelta(width,height);node:SetLocalScale(scale/advance,scale/line,1)
   node:SetAnchoredPosition((width/2-2+(chunk.x-data.anchor[1])*advance)*scale/advance,((data.anchor[2]-chunk.y)*line-height/2)*scale/line)
  end
 end
 c.frame=data;c.scale=scale
end
`+lua.slice(end);
lua=lua.replaceAll('GF10-TEXT-AVATAR-V2','GF10-TEXT-AVATAR-V3').replaceAll('TEXT-AVATAR-V2 /','TEXT-AVATAR-V3 /');
save.assets.scripts[0].source=lua;save.assets.scripts[0].filename='gpt_20261005_头像短文本V3.lua';save.assets.scripts[0].path='lua/'+save.assets.scripts[0].filename;
save.assets.server.root.name='gpt_20261005_头像短文本V3_A';save.assets.server.meta.name=save.assets.server.root.name;save.assets.server.meta.giaFileName=save.assets.server.root.name+'.gia';
fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(save));fs.writeFileSync(out+'/完整游戏.lua',lua);
const native=JSON.parse(fs.readFileSync('outputs/text-avatars-display-v2-20261005/fighter.save.json'));native.assets.server=structuredClone(save.assets.server);native.assets.scripts=structuredClone(save.assets.scripts);fs.writeFileSync(out+'/fighter.save.json',JSON.stringify(native));
const result=exportGia(native.assets.server,{scripts:native.assets.scripts});assert(validateServerGiaCompatibility(result.buffer).valid);assert(importGia(result.buffer,save.assets.server.meta.giaFileName).scripts.some(s=>s.source===lua));fs.writeFileSync(out+'/'+save.assets.server.meta.giaFileName,result.buffer);
fs.writeFileSync(out+'/report.json',JSON.stringify({maxChunkBytes:1000,totalTextPoolControls:totalControls,pools,frames:reports,nativePortraitVerified:false,nativeGeometryVerified:false,sourceVisiblePixelsPreserved:true,actorAndStagePoolsUnchanged:true},null,2));
fs.writeFileSync(out+'/说明.md','# 头像短文本V3候选\n\n首页两图和选人头像分成短富文本块，每块UTF-8不超过1000字节；保留原网格、有效像素、透明与颜色，去掉全透明块。复用各显示槽的文本控件，换图时更新并隐藏空闲控件。沿用V2加载遮罩和错误面板。\n\n真机：短文本、大小写和缩放可用；约8.6KB起的长度探针预置和Lua赋值均显示标签原文。尚不能确定是字节数还是标签数量边界。V3完整头像拼接、字号字距和接缝待真机验收。\n\n同一存档只替换A。B和GF10节点保持当前已配置版本；A中PIXEL_TEMPLATE_INDEX须使用该存档的B外层容器实际索引，默认1073742822不代表新存档实际值。\n');
console.log(JSON.stringify({totalControls,maxBytes:Math.max(...reports.map(r=>r.maxUtf8Bytes)),home:reports.filter(r=>r.family==='home')}));
