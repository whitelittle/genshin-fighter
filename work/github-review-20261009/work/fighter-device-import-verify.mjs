import {readFileSync,writeFileSync} from 'node:fs';import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {renderPaintPng} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';
function state(s){const r=s.playGet({view:true});assert.equal(r.logs.filter(l=>['error','lua-error'].includes(l.level)).length,0,JSON.stringify(r.logs));return r;}
const find=(s,name)=>state(s).scene.nodes.find(n=>n.name===name);
const step=(s,n)=>{for(let i=0;i<n;i++)s.playStep(1/30,{observe:false});state(s);};
const shot=(s,path)=>{const r=s.playGet({view:true,paint:true});writeFileSync(path,renderPaintPng(r.paint,r.canvasWidth,r.canvasHeight).data);};
for(const mode of ['solo','online']){
 const out=`outputs/demo-${mode}-light-importfix`,save=JSON.parse(readFileSync(out+'/fighter.save.json')),build=JSON.parse(readFileSync(out+'/build.json'));
 assert.ok(!/[^\x09\x0a\x20-\x7e]/.test(save.assets.scripts[0].source));
 const loaded=createStudio();loaded.importData('gia',readFileSync(out+'/'+build.filename).toString('base64'),build.filename);loaded.playStart({playerCount:mode==='online'?2:1});step(loaded,1);assert.ok(find(loaded,'BootDiagnostic').text.includes('Lua 已启动'));assert.ok(state(loaded).scene.nodes.filter(n=>/^P\d+$/.test(n.name)).length>=2648);shot(loaded,out+'/导入后启动.png');
 const noLua=structuredClone(save);noLua.assets.scripts=[];const passive=createStudio(noLua);passive.playStart();assert.equal(find(passive,'BootDiagnostic').text,'界面已导入，等待 Lua 启动');shot(passive,out+'/无脚本静态诊断.png');
 if(mode==='online'){
  assert.ok(find(loaded,'Status').text.includes('等待双人模式'),'GIA must still require server logic');const net=createStudio(save);net.playStart({playerCount:2});net.playSetView(1);net.playClick('Light',{observe:false});step(net,6);net.playPause();const a=net.playSetView(1,{view:true,paint:true}),b=net.playSetView(2,{view:true,paint:true});assert.deepEqual(a.scene.nodes,b.scene.nodes);assert.ok(renderPaintPng(a.paint,a.canvasWidth,a.canvasHeight).data.equals(renderPaintPng(b.paint,b.canvasWidth,b.canvasHeight).data));assert.ok(find(net,'Stats').text.includes('100 / 92'));
 }
 else {
  const d=structuredClone(save);d.assets.scripts[0].source+='\nlocal previousStart=OnStart\nfunction OnStart()previousStart();aiEnabled=false;f[1].x=-40;f[2].x=40;f[1].meter=100;draw()end';const s=createStudio(d);s.playStart();for(let q=0;q<2;q++)for(const k of ['KeyboardMoveBackwardKeyDown','KeyboardMoveRightKeyDown','KeyboardMoveBackwardKeyUp','KeyboardMoveRightKeyUp'])s.playKey(k,{observe:false});s.playKey('KeyboardCraftspersonKey20Down',{observe:false});s.playKey('KeyboardCraftspersonKey20Up',{observe:false});step(s,13);assert.ok(find(s,'Stats').text.includes('100 / 62'));
  const bad=structuredClone(save);bad.assets.server.root.children[0].children=bad.assets.server.root.children[0].children.filter(n=>n.name!=='Keqing');const errorScene=createStudio(bad);errorScene.playStart();assert.ok(find(errorScene,'BootDiagnostic').text.startsWith('INIT ERROR:'));shot(errorScene,out+'/缺少层级时错误可见.png');
 }
 writeFileSync(out+'/verification.json',JSON.stringify({simulatorVerified:true,deviceVerified:false,tests:{asciiLua:true,giaReimportFullHierarchy:true,visibleStaticMessageWithoutLua:true,bootMessageWithLua:true,gameplayPreserved:true,onlinePausePixelEquality:mode==='online',visibleInitError:mode==='solo'}},null,2));console.log(mode+' import-fix tests passed');
}
