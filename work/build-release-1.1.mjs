import fs from 'node:fs';
import assert from 'node:assert/strict';
import {exportGia,importGia,validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
// Release 1.1. Device conclusion (P1 102231): even with no menus the phone crashes holding the ~934k-glyph training
// room, so it is dropped. Built on D5 (menus inactive only while loading battle, side covers, error keeps backing):
// portrait frames return for selection and battle, the battle background is four flat image faces, and the loading
// diagnostic line is switched off.
const VERSION='1.1';
const base=JSON.parse(fs.readFileSync('work/mobile-load-diagnostic-latest.json'));
assert.equal(base.variant,'battle-deactivate-cover');
const save=JSON.parse(fs.readFileSync(base.out+'/simulator.save.json'));
const native=JSON.parse(fs.readFileSync(base.out+'/fighter.save.json'));
const GUID_LIMIT=1073741824+4194304,GUID_START=1077800000;
let guid=GUID_START;
const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean);

function patchLua(lua){
 const once=(from,to)=>{assert.equal(lua.split(from).length,2,'anchor: '+from.slice(0,70));lua=lua.replace(from,()=>to);};
 const pd=/^local portraitData=.*$/m;assert.equal((lua.match(pd)||[]).length,1,'portraitData');lua=lua.replace(pd,()=>portraitLine);
 once(" if loadingTarget=='battle' or resourceGate.waitingForBattle() then\n  local s=resourceGate.loader.stats"," if false then\n  local s=resourceGate.loader.stats");
 // Selection portraits are drawn at 2.7*48/w, battle portraits at 1.45*48/w; frames scale with them.
 once("local portrait=rootNode('Portrait'..i);portrait:SetVisible(false)","local portrait=rootNode('Portrait'..i);portrait:SetVisible(selecting or fighting)");
 once("for _,part in ipairs(portrait:GetChildren())do if string.match(part.name,'^PortraitFrame')then part:SetVisible(fighting)end end;",
  "do local k=selecting and 2.7/1.45 or 1;for _,part in ipairs(portrait:GetChildren())do local side=string.match(part.name,'^PortraitFrame(%a+)$');if side then part:SetVisible(fighting or selecting);if side=='Back'then part:SetSizeDelta(86*k,86*k)elseif side=='Top'or side=='Bottom'then part:SetSizeDelta(86*k,3);part:SetAnchoredPosition(0,(side=='Top'and 41.5 or -41.5)*k)else part:SetSizeDelta(3,80*k);part:SetAnchoredPosition((side=='Right'and 41.5 or -41.5)*k,0)end end end end;");
 once("for _,name in ipairs({'Stats','Timer','Status','TopPanel',","if fighting then resourceGate.layoutArena()end\n for _,name in ipairs({'ArenaFaces','Stats','Timer','Status','TopPanel',");
 const md=/local function menuDraw\(\)[ \t\r]*\n/g;assert.equal((lua.match(md)||[]).length,1,'menuDraw');
 lua=lua.replace(md,()=>`resourceGate.layoutArena=function()
 local a=rootNode('ArenaFaces');a:SetAsFirstSibling();local cw,ch=game.GetUICanvasSize();local key=cw..':'..ch;if resourceGate.arenaKey==key then return end;resourceGate.arenaKey=key
 local fy=Collision.floorY();local side=cw*.07
 local wall=a:FindChild('ArenaWall');wall:SetSizeDelta(cw*2,ch*2);wall:SetAnchoredPosition(0,fy+ch)
 local floor=a:FindChild('ArenaFloor');floor:SetSizeDelta(cw*2,ch*2);floor:SetAnchoredPosition(0,fy-ch)
 for i,name in ipairs({'ArenaLeft','ArenaRight'})do local n=a:FindChild(name);local dir=i==1 and -1 or 1;n:SetSizeDelta(cw*.5+side,ch*3);n:SetAnchoredPosition(dir*(cw*.75-side/2),0)end
end
local function menuDraw()
`);
 return lua;
}

const fullOut=JSON.parse(fs.readFileSync('work/full-art-return-latest.json')).out;
const fullNative=JSON.parse(fs.readFileSync(fullOut+'/fighter.save.json'));
const portraitLine=fullNative.assets.scripts[0].source.split('\n').find(l=>l.startsWith('local portraitData='));
assert(portraitLine&&portraitLine.length>1000,'052337 portraitData');
const portraitArts=(find(fullNative.assets.server.root,'Portrait1').children||[]).filter(c=>/^TextArt\d+$/.test(c.name));
assert(portraitArts.length>100,'052337 portrait TextArt');

const host=find(native.assets.server.root,'FighterDemo');assert(host);
const title=find(host,'GameTitle');assert(title&&title.text==='原神格斗1.0');title.text='原神格斗'+VERSION;
const proto=find(host,'Hp1');assert(proto&&proto.kind==='image');
function image(name,color,size,offset){const n=structuredClone(proto);n.id='ui_'+guid;n.guid=guid++;n.name=name;n.children=[];n.visible=true;n.active=true;n.imageColor=color;n.raycastTarget=false;delete n.scriptMappingIds;delete n.giaRelatedGuids;delete n.giaInfoIndex;
 for(const t of Object.values(n.transformByPlatform)){t.anchorMin={x:.5,y:.5};t.anchorMax={x:.5,y:.5};t.pivot={x:.5,y:.5};t.offset=offset;t.size=size;t.scale={x:1,y:1,z:1};t.rotation={x:0,y:0,z:0};}return n;}
for(let p=1;p<=2;p++){
 const parent=find(host,'Portrait'+p);assert(parent);assert(!(parent.children||[]).some(c=>/^PortraitFrame/.test(c.name)));
 const color=p===1?0xff8bcaff:0xffffa4a4;
 // Back first, edges above it; runtime portrait pixels are moved to last sibling and draw on top.
 const parts=[image('PortraitFrameBack',0xff19283a,{x:86,y:86},{x:0,y:0})];
 for(const [name,x,y,w,h] of [['Top',0,41.5,86,3],['Bottom',0,-41.5,86,3],['Left',-41.5,0,3,80],['Right',41.5,0,3,80]])parts.push(image('PortraitFrame'+name,color,{x:w,y:h},{x,y}));
 for(const n of parts)n.visible=false;
 const arts=portraitArts.map(src=>{const n=structuredClone(src);n.id='ui_'+guid;n.guid=guid++;n.visible=false;n.text='';n.scriptMappingIds=[];n.giaRelatedGuids=[];delete n.giaInfoIndex;return n;});
 parent.children=[...arts,...parts];
}
const container=structuredClone(find(host,'SelectScreen'));container.id='arena_faces';container.guid=guid++;container.name='ArenaFaces';container.visible=false;container.active=true;delete container.scriptMappingIds;delete container.giaRelatedGuids;delete container.giaInfoIndex;
container.children=[image('ArenaWall',0xff33465e,{x:3200,y:1440},{x:0,y:500}),image('ArenaFloor',0xff4a4f5a,{x:3200,y:1440},{x:0,y:-940}),image('ArenaLeft',0xff222e40,{x:900,y:2160},{x:-1100,y:0}),image('ArenaRight',0xff222e40,{x:900,y:2160},{x:1100,y:0})];
host.children=[...host.children,container];
const inBand=n=>(n.guid==null||n.guid<GUID_LIMIT)&&(n.children||[]).every(inBand);assert(inBand(native.assets.server.root),'GUID out of band');
const guids=[];const all=n=>{if(n.guid!=null)guids.push(n.guid);(n.children||[]).forEach(all)};all(native.assets.server.root);assert.equal(new Set(guids).size,guids.length,'duplicate GUID');

const deviceLua=patchLua(native.assets.scripts[0].source);
const simLua=patchLua(save.assets.scripts[0].source);
const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date()).map(v=>[v.type,v.value]));
const stamp=p.year+p.month+p.day+'_'+p.hour+p.minute+p.second,out='outputs/release-'+VERSION+'-'+stamp,name='gpt_'+stamp+'_原神格斗'+VERSION+'_A';
fs.mkdirSync(out,{recursive:true});
for(const s of native.assets.scripts){s.source=deviceLua;s.filename=name+'.lua';s.path=name+'.lua';}
native.assets.server.root.name=name;native.assets.server.meta.name=name;native.assets.server.meta.giaFileName=name+'.gia';
native.meta={...native.meta,name:'原神格斗'+VERSION};
const a=exportGia(native.assets.server,{scripts:native.assets.scripts});assert(validateServerGiaCompatibility(a.buffer).valid);
fs.writeFileSync(out+'/'+name+'.gia',a.buffer);fs.writeFileSync(out+'/fighter.save.json',JSON.stringify(native));fs.writeFileSync(out+'/完整游戏.lua',deviceLua);
const aa=importGia(a.buffer,name+'.gia');assert.equal(aa.scripts[0].source,deviceLua);
save.meta={...save.meta,name:native.meta.name};save.assets.server=aa.project;save.assets.scripts=aa.scripts.map(s=>({...s,source:simLua}));
for(const s of save.assets.scripts){const hits=[];const walk=n=>{if((n.scriptMappingIds||[]).includes(s.guid))hits.push(n);for(const c of n.children||[])walk(c);};walk(aa.project.root);assert.equal(hits.length,1);s.controlId=hits[0].id;}
fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(save));
let controls=0;const count=n=>{controls++;(n.children||[]).forEach(count)};count(aa.project.root);
const report={version:VERSION,base:base.out,initialClientControls:controls-1,addedControls:guid-GUID_START,guidRange:[GUID_START,guid-1],sourceBytes:Buffer.byteLength(deviceLua),giaABytes:a.buffer.length,deviceVerified:false};
fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2));
fs.writeFileSync(out+'/实机测试说明.md',`# 原神格斗 ${VERSION}\n\n基于 D5（只在战斗加载时停用菜单、两侧遮挡、出错时保留背景并显示错误）。相对 D5 的变化：\n\n- 从052337加回选人/战斗大头像的文字块与portraitData（不含训练室）。选人页点角色后两侧预览头像应显示。\n- 选人页和战斗中两侧头像加回头像框（底板加四条边，共 10 个图片控件），选人时按头像放大比例放大。\n- 战斗背景改为四个纯色面：后墙、地面、左右侧墙。地面线与角色站立高度一致，宽度超出画布。不再使用训练室。\n- 关闭读条下方的诊断文字。\n- 首页标题改为「原神格斗${VERSION}」。\n\n客户端控件 ${report.initialClientControls} 个（含两侧大头像文字块），新增 ${report.addedControls} 个，GUID ${report.guidRange[0]}–${report.guidRange[1]}，都在编辑器可接受的范围内。B 外层索引已写入，无需手改。\n\n## 导入\n\n双方 A 换成 ${name}.gia，B、GF10 和变量照旧，不需要 C。\n`);
fs.writeFileSync('work/release-latest.json',JSON.stringify({out,name,stamp,version:VERSION,base:base.out},null,2));
console.log(JSON.stringify({out,name,...report}));
