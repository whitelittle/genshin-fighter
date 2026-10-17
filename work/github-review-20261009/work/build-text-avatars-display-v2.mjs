import fs from 'node:fs';import assert from 'node:assert/strict';
import {exportGia,validateServerGiaCompatibility,importGia} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const out='outputs/text-avatars-display-v2-20261005';fs.mkdirSync(out,{recursive:true});
const save=JSON.parse(fs.readFileSync('outputs/text-avatars-20261005/simulator.save.json'));let source=save.assets.scripts[0].source;
const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean);
const host=find(save.assets.server.root,'FighterDemo');
function walk(n){if(n.name==='TextArt'){delete n.giaRaw.textAlign;delete n.giaRaw.textVerticalAlign;}for(const c of n.children||[])walk(c);}walk(host);
const errorNode=structuredClone(find(host,'LoadingText'));errorNode.id='text_v2_error';errorNode.guid=1073930001;errorNode.name='RuntimeError';errorNode.text='';errorNode.visible=false;errorNode.fontSize=22;errorNode.minimumFontSize=22;errorNode.bgColor=0xff101b2c;errorNode.enableOutline=false;errorNode.horizontalAlignment='Left';errorNode.verticalAlignment='Top';delete errorNode.giaRaw.textAlign;delete errorNode.giaRaw.textVerticalAlign;for(const t of Object.values(errorNode.transformByPlatform)){t.anchorMin={x:.5,y:.5};t.anchorMax={x:.5,y:.5};t.offset={x:0,y:0};t.size={x:1400,y:600};}host.children.unshift(errorNode);
function rep(a,b){assert(source.includes(a),'Missing '+a.slice(0,100));source=source.replace(a,()=>b);}
rep("resourceGate.waitingForBattle=function()return menuMode=='roundload'end", "resourceGate.waitingForBattle=function()return menuMode=='roundload' or menuMode=='waitingRound'end");
rep('resourceGate.loader.syncCover=function()\n',`resourceGate.loader.fail=function(message)
 loadingState='error'
 local panel=loadingRoot:FindChild('RuntimeError')
 for _,node in ipairs(loadingRoot:GetChildren())do node:SetVisible(node==panel)end
 local cw,ch=game.GetUICanvasSize();panel:SetSizeDelta(cw*.9,ch*.8);panel:SetAnchoredPosition(0,0)
 panel.text='TEXT-AVATAR-V2 / Lua error\\n'..tostring(message)..'\\nB index='..PIXEL_TEMPLATE_INDEX..' / target='..loadingTarget..' / tasks='..loadingDone..'/'..loadingTotal
 panel:SetVisible(true);print('[RESOURCE ERROR] '..tostring(message))
end
resourceGate.loader.syncCover=function()
 local backing=loadingRoot:FindChild('FullscreenBacking')
 if backing then backing:SetVisible(loadingState=='ready' and not resourceGate.waitingForBattle())end
`);
rep("if waiting then loadingOverlay:FindChild('LoadingBlack'):SetVisible(true);loadingDraw(0)end", "if waiting and not resourceGate.loader.wasWaiting then loadingOverlay:FindChild('LoadingBlack'):SetVisible(true);resourceGate.loader.displayClock=.1;loadingDraw(0)end\n resourceGate.loader.wasWaiting=waiting");
rep("resourceGate.loader.coverVisible=true;loadingOverlay:SetVisible(true);", "resourceGate.loader.coverVisible=true;loadingRoot:FindChild('FullscreenBacking'):SetVisible(false);loadingOverlay:SetActive(true);loadingOverlay:SetVisible(true);");
rep("if loadingState=='ready'then\n  loadedUpdate(dt)\n  if loadingState=='ready'then resourceGate.backgroundPrepare()end\n  resourceGate.loader.syncCover();return\n end\n local ok,message=pcall(function()", `local ok,message=pcall(function()
  if loadingState=='error' then return end
  if loadingState=='ready'then
   loadedUpdate(dt)
   if loadingState=='ready'then resourceGate.backgroundPrepare()end
   resourceGate.loader.syncCover();return
  end`);
const errorAt=source.lastIndexOf(" if not ok then loadingState='error';");assert(errorAt>0);const errorEnd=source.indexOf('\nend',errorAt);source=source.slice(0,errorAt)+" if not ok then resourceGate.loader.fail(message)end"+source.slice(errorEnd);
source=source.replaceAll('GF10-TEXT-AVATAR','GF10-TEXT-AVATAR-V2');
save.assets.scripts[0].source=source;save.assets.scripts[0].path='lua/gpt_20261005_头像显示排错V2.lua';save.assets.scripts[0].filename='gpt_20261005_头像显示排错V2.lua';save.assets.server.root.name='gpt_20261005_头像显示排错V2_A';save.assets.server.meta.name=save.assets.server.root.name;save.assets.server.meta.giaFileName=save.assets.server.root.name+'.gia';
fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(save));fs.writeFileSync(out+'/完整游戏.lua',source);
const native=JSON.parse(fs.readFileSync('outputs/text-avatars-20261005/fighter.save.json'));native.assets.server=structuredClone(save.assets.server);native.assets.scripts=structuredClone(save.assets.scripts);fs.writeFileSync(out+'/fighter.save.json',JSON.stringify(native));
const result=exportGia(native.assets.server,{scripts:native.assets.scripts});assert(validateServerGiaCompatibility(result.buffer).valid);assert(importGia(result.buffer,save.assets.server.meta.giaFileName).scripts.some(s=>s.source===source));fs.writeFileSync(out+'/'+save.assets.server.meta.giaFileName,result.buffer);
fs.writeFileSync(out+'/说明.md','# 头像显示排错V2候选\n\n清除原始居中字段；加载时隐藏新增底层背景，排除覆盖遮罩的可能；将原来未保护的ready阶段更新纳入错误捕获；错误显示在独立纯文本面板；等待下一回合也保留遮罩。未变更富文本颜色语法：需先验独立校准包再选择解析路径，不能标为头像显示已修复。\n\n程序/GIA检查见本目录。真机：旧文本头像版加载很快，但标签直出，双方确认后底色持续超过一分钟；V2尚未真机验收。B索引仍待核对，默认1073742822。\n');console.log('TEXT_DISPLAY_DIAGNOSTIC_V2_EXPORTED');
