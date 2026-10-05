import fs from 'node:fs';import {createServer}from'node:http';import {createRequire}from'node:module';
import {createStudio}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
const base=process.env.V4_PREVIEW_BASE||'outputs/original-text-training-v4-20261005',out=base+'/visual-simulator';fs.mkdirSync(out,{recursive:true});
const report=JSON.parse(fs.readFileSync(base+'/report.json')),save=JSON.parse(fs.readFileSync(base+'/simulator.save.json'));
let total=0;for(const [prefix,family]of [['resourceGate.homePortraitData=','home'],['local portraitData=','portrait'],['local thumbData=','thumb'],['local Collision=','stage']]){
 const line=save.assets.scripts[0].source.split('\n').find(l=>l.startsWith(prefix)),ordered=report.allFrames.filter(r=>r.family===family);let index=0;
 const next=line.replace(/\{textArt=true,palette=\{[^}]*\},chunks=\{.*?\},w=(\d+),h=(\d+),scale=([^,]+),anchor=\{([^}]*)\}\}/g,(_,w,h,scale,anchor)=>'{textArt=true,preview="'+ordered[index++].key+'",chunks={{}},w='+w+',h='+h+',scale='+scale+',anchor={'+anchor+'}}');
 if(index!==ordered.length)throw Error('Preview frame count '+family);total+=index;save.assets.scripts[0].source=save.assets.scripts[0].source.replace(line,()=>next);
}if(total!==report.allFrames.length)throw Error('Preview total');
function walk(n){if((n.children||[]).some(c=>/^TextArt\d+$/.test(c.name)))n.children=n.children.filter(c=>!/^TextArt\d+$/.test(c.name)||c.name==='TextArt1');for(const c of n.children||[])walk(c);}walk(save.assets.server.root);
const begin=save.assets.scripts[0].source.indexOf('resourceGate.textArtCache={}'),end=save.assets.scripts[0].source.indexOf('local function paintFrame(',begin);
save.assets.scripts[0].source=save.assets.scripts[0].source.slice(0,begin)+`resourceGate.textArtCache={}
resourceGate.textNodes=function(parent)
 local c=resourceGate.textArtCache[parent.name];if not c then c={node=parent:FindChild('TextArt1')};resourceGate.textArtCache[parent.name]=c end;return c
end
resourceGate.paintTextChunk=function(parent,data,scale,i)
 if i~=1 then return end
 local c=resourceGate.textNodes(parent);local inset=0;c.node.text='RASTER:'..data.preview;c.node:SetSizeDelta(data.w*scale,data.h*scale);c.node:SetLocalScale(1,1,1);c.node:SetAnchoredPosition(inset,inset);c.node:SetVisible(true);c.frame=data;c.scale=scale
end
resourceGate.paintTextArt=function(parent,data,scale)
 local c=resourceGate.textNodes(parent);if c.frame==data and c.scale==scale then return end;resourceGate.paintTextChunk(parent,data,scale,1)
end
`+save.assets.scripts[0].source.slice(end);
fs.writeFileSync(out+'/preview-only.save.json',JSON.stringify(save));
let renderer=fs.readFileSync('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js','utf8');
renderer=renderer.replace("from './play/image-fill.js'","from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/play/image-fill.js'");
renderer=renderer.replace('const require = createRequire(import.meta.url)',"const require = createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json')");
renderer=renderer.replace('function drawTextItem(ctx, item, width, height) {',`let rasterImages=new Map();export function setRasterImages(images){rasterImages=images}
function drawTextItem(ctx,item,width,height){
 if(String(item.text||'').startsWith('RASTER:')){const image=rasterImages.get(item.text.slice(7));if(image){ctx.imageSmoothingEnabled=false;ctx.drawImage(image,-width/2,-height/2,width,height)}return}
`);fs.writeFileSync(out+'/raster-renderer.mjs',renderer);
const{renderPaintPng,setRasterImages}=await import('../'+out+'/raster-renderer.mjs');
const req=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json');const{loadImage}=req('@napi-rs/canvas');
const images=new Map();for(const item of report.allFrames)images.set(item.key,await loadImage(base+'/rasters/'+item.key+'.png'));setRasterImages(images);
let studio,mode='home',busy=false,view=1,lastError='',paused=false;
const state=()=>studio.playGet({view:true});
const has=name=>state().scene.nodes.some(n=>n.name===name);
const step=n=>{for(let i=0;i<n;i++)studio.playStep(1/60,{observe:false});};
function settle(){for(let i=0;i<16000;i+=20){if(!has('LoadingBar'))return;step(20);}throw Error('Loading timeout');}
function click(player,name){studio.playSetView(player);let node=state().scene.nodes.find(n=>n.name===name);if(!node)throw Error('Missing '+name);const nodes=state().scene.nodes;let x=0,y=0;while(node){const ox=x,oy=y;x=node.matrix.a*ox+node.matrix.c*oy+node.matrix.tx;y=node.matrix.b*ox+node.matrix.d*oy+node.matrix.ty;node=nodes.find(n=>n.id===node.parent);}studio.playPointer('click',x,y,{observe:false});step(1);}
function page(next){if(studio)studio.playStop();studio=createStudio(save);studio.playStart({playerCount:2,canvasId:'pc-16-9'});mode=next;view=1;settle();
 if(next!=='home'){for(let p=1;p<=2;p++){studio.playSetView(p);settle();click(p,'StartDuel');settle();}}
 if(next==='battle'){for(let p=1;p<=2;p++)for(const role of p===1?[1,3,5]:[2,4,6]){settle();click(p,'GridCard'+role);step(20);}click(1,'ReadyConfirm');step(100);click(2,'ReadyConfirm');for(let i=0;i<16000&&!has('Timer');i+=20)step(20);if(!has('Timer'))throw Error('Battle transition timeout');}
 studio.playSetView(view);const errors=state().logs.filter(l=>['error','lua-error'].includes(l.level));if(errors.length)throw Error(JSON.stringify(errors));}
page('home');
const html=`<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>原图文字V4 · 模拟器预览</title><style>body{margin:0;background:#10131b;color:#edf2f8;font:14px system-ui}header{padding:12px 20px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}button{background:#263c60;color:white;border:1px solid #688ab9;border-radius:7px;padding:8px 14px;cursor:pointer}small{color:#b2bdce}#screen{display:block;width:min(100vw,1600px);margin:auto;outline:none}#status{padding:8px 20px}</style><header><b>原图文字V4 · 模拟器</b><button data-page="home">封面</button><button data-page="select">选人</button><button data-page="battle">训练室对战</button><button id="view">切换玩家</button><button id="pause">暂停 / 继续</button><small>采样图替代富文本显示；用于看构图与流程，不能验收真机接缝或加载耗时。</small></header><img id="screen" tabindex="0" alt="双人游戏模拟器"><div id="status">正在加载预览…</div><script src="/app.js"></script></html>`;
const js=`const screen=document.querySelector('#screen'),status=document.querySelector('#status');let pending=false;async function act(body){pending=true;status.textContent='正在切换…';try{const r=await fetch('/action',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});const v=await r.json();status.textContent=v.error||('页面：'+v.mode+' · 玩家'+v.view);screen.focus()}finally{pending=false}}document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>act({page:b.dataset.page}));document.querySelector('#view').onclick=()=>act({switchView:true});document.querySelector('#pause').onclick=()=>act({pause:true});screen.onclick=e=>{const r=screen.getBoundingClientRect();act({click:[(e.clientX-r.left)/r.width*1600,900-(e.clientY-r.top)/r.height*900]})};screen.onkeydown=e=>{e.preventDefault();fetch('/action',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({key:e.key,down:true})})};screen.onkeyup=e=>{e.preventDefault();fetch('/action',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({key:e.key,down:false})})};screen.onload=()=>setTimeout(()=>{if(!pending)screen.src='/screen.png?t='+Date.now();else screen.onload()},120);screen.onerror=()=>setTimeout(()=>screen.src='/screen.png?t='+Date.now(),500);screen.src='/screen.png';status.textContent='页面：home · 玩家1';`;
const server=createServer(async(req,res)=>{try{if(req.url==='/'){res.writeHead(200,{'content-type':'text/html;charset=utf-8'});res.end(html);return}if(req.url==='/app.js'){res.writeHead(200,{'content-type':'text/javascript;charset=utf-8'});res.end(js);return}if(req.url.startsWith('/screen.png')){const r=studio.playGet({view:true,paint:true});const png=renderPaintPng(r.paint,r.canvasWidth,r.canvasHeight).data;res.writeHead(200,{'content-type':'image/png','cache-control':'no-store'});res.end(png);return}if(req.method==='POST'&&req.url==='/action'){let body='';for await(const c of req){body+=c;if(body.length>2000)throw Error('Request too large')}const a=JSON.parse(body);busy=true;try{if(a.page)page(a.page);if(a.switchView){view=3-view;studio.playSetView(view)}if(a.pause)paused=!paused;if(a.click)studio.playPointer('click',...a.click,{observe:false});if(a.key)studio.playKey(a.key,a.down,{observe:false});}finally{busy=false}res.writeHead(200,{'content-type':'application/json'});res.end(JSON.stringify({mode,view,error:lastError}));return}res.writeHead(404);res.end();}catch(e){lastError=String(e.message);res.writeHead(500,{'content-type':'application/json'});res.end(JSON.stringify({error:lastError}));}});
setInterval(()=>{if(!busy&&!paused)try{step(2)}catch(e){lastError=String(e.message);paused=true}},33);
const port=Number(process.env.V4_PREVIEW_PORT||4202);server.listen(port,'127.0.0.1',()=>console.log('V4_VISUAL_SIMULATOR http://127.0.0.1:'+port));
fs.writeFileSync(out+'/说明.md','此预览运行同一游戏模拟器逻辑，高清文字显示槽使用采样PNG替代。预览save不用于GIA导出；加载任务减少，不可比较原生性能或宣称文字接缝通过。正式候选仍是上级目录V4 A。\n');
