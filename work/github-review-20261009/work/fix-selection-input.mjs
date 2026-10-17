import fs from 'node:fs';
import assert from 'node:assert/strict';
const out=process.env.REPAIR_OUT||'outputs/midphase-final';
const index=Number(process.env.PIXEL_TEMPLATE_INDEX||1073742822);
const updated=[];
for(const filename of ['fighter.save.json','simulator.save.json']){
 const file=out+'/'+filename,save=JSON.parse(fs.readFileSync(file));
 let serial=0;const controls=[];
 function visit(n){
  const menuControl=/^(GridCard\d+|TeamSlot\d+|PagePrev|PageNext|ReadyConfirm|BackHome|Rematch|Reselect|ResultHome|DebugToggle|CommandToggle|CommandClose|ExitMatch)$/.test(n.name);
  if(!menuControl&&n.children?.some(c=>c.name==='InputHit'))n.children=n.children.filter(c=>c.name!=='InputHit');
  if(menuControl&&(n.kind==='cursor'||n.kind==='container')&&n.children?.length&&!n.children.some(c=>c.name==='InputHit')){
   const hit=structuredClone(n);hit.id='selection_input_hit_'+(++serial);hit.guid=1076800000+serial;hit.name='InputHit';hit.children=[];hit.raycastTarget=true;hit.active=true;hit.visible=true;delete hit.scriptMappingIds;
   for(const t of Object.values(hit.transformByPlatform)){t.offset={x:0,y:0};t.size={x:0,y:0};t.anchorMin={x:0,y:0};t.anchorMax={x:1,y:1};t.pivot={x:.5,y:.5};t.scale={x:1,y:1,z:1};}
   n.children.unshift(hit);controls.push(n.name);
  }
  if(menuControl&&n.children?.some(c=>c.name==='InputHit')){n.kind='container';n.raycastTarget=false;}
  for(const c of n.children||[])if(c.name!=='InputHit')visit(c);
 }
 visit(save.assets.server.root);
 let source=save.assets.scripts[0].source;
 const before="local function menuBind(name,callback)rootNode(name):AddCursorEventListener(Enum.CursorEventType.CursorClick,callback)end";
 const previous="local function menuBind(name,callback)local control=rootNode(name);local hit=control:FindChild('InputHit')or control;hit:AddCursorEventListener(Enum.CursorEventType.CursorClick,callback)end";
 const invalid="local function menuBind(name,callback)local control=rootNode(name);local hit=control:FindChild('InputHit');local lastClick=-1;local function once()if lastClick==menuTime then return end;lastClick=menuTime;callback()end;control:AddCursorEventListener(Enum.CursorEventType.CursorClick,once);if hit then hit:AddCursorEventListener(Enum.CursorEventType.CursorClick,once)end end";
 const after="local function menuBind(name,callback)local control=rootNode(name);local hit=control:FindChild('InputHit')or control;hit:AddCursorEventListener(Enum.CursorEventType.CursorClick,callback)end";
 source=source.replace(invalid,after);
 assert(source.includes(before)||source.includes(previous)||source.includes(after),'menu binding target');source=source.replace(before,after).replace(previous,after);
 source=source.replace(/local PIXEL_TEMPLATE_INDEX=\d+/,'local PIXEL_TEMPLATE_INDEX='+index);
 const gate="if menuMode~='select'or resourceGate.busy or menuReady[seat]or(seat~=1 and seat~=2)then return end";
 const reason="if menuMode~='select' then return end\n if seat~=1 and seat~=2 then rootNode('SelectionHint').text='等待服务器分配席位：FighterHello → FighterSeat';print('[SELECT INPUT] blocked: no FighterSeat');helloRequest();return end\n if resourceGate.busy or menuReady[seat]then return end";
 assert(source.includes(gate)||source.includes(reason),'selection gate target');source=source.replace(gate,reason);
 save.assets.scripts[0].source=source;
 if(filename==='simulator.save.json')save.assets.client.root.children[0].guid=index;
 fs.writeFileSync(file,JSON.stringify(save));updated.push({filename,controls,index});
}
fs.writeFileSync(out+'/selection-input-fix.json',JSON.stringify({updated,controlEntity:1077936129,pixelTemplateIndex:index,officialVerified:false,description:'Independent empty cursor above decorative children; explicit missing-seat feedback'},null,2));
console.log(JSON.stringify(updated.map(x=>({file:x.filename,controls:x.controls.length,index}))));
