import {readFileSync as read,writeFileSync as write} from 'node:fs';
import assert from 'node:assert/strict';
import {packFrame,luaFrame} from './v2-pack.mjs';
const out=process.env.GROUP1_OUT||'outputs/group1-full-test',save=JSON.parse(read(out+'/base.save.json'));
function find(n,name){if(n.name===name)return n;for(const c of n.children||[]){const r=find(c,name);if(r)return r;}}
const host=find(save.assets.server.root,'FighterDemo'),home=find(host,'HomeScreen'),image=find(host,'Hp1'),text=find(host,'GameTitle'),group=find(host,'Art');let serial=0;
function transform(n,x,y,w,h){for(const t of Object.values(n.transformByPlatform)){t.offset={x,y};t.size={x:w,y:h};t.scale={x:1,y:1,z:1};t.rotation={x:0,y:0,z:0};t.anchorMin=t.anchorMax=t.pivot={x:.5,y:.5};}return n;}
function stretch(n){for(const t of Object.values(n.transformByPlatform)){t.anchorMin={x:0,y:0};t.anchorMax={x:1,y:1};t.offset={x:0,y:0};t.size={x:0,y:0};}return n;}
function add(proto,name,x,y,w,h,parent){const n=structuredClone(proto);n.id='home10_'+(++serial);n.guid=1076000000+serial;n.name=name;n.children=[];n.active=n.visible=true;n.raycastTarget=false;delete n.scriptMappingIds;transform(n,x,y,w,h);parent.children.unshift(n);return n;}
function box(name,x,y,w,h,color,parent){const n=add(image,name,x,y,w,h,parent);n.imageColor=Number('0xff'+color)>>>0;return n;}
function label(name,str,x,y,w,h,size,parent){const n=add(text,name,x,y,w,h,parent);n.text=str;n.fontSize=size;n.minimumFontSize=size;n.enableOutline=false;return n;}
function capsule(name,w,h,color,parent,y=0){const r=h/2;for(let k=0;k<h;k+=2){const py=k+1-r,half=w/2-r+Math.sqrt(Math.max(0,r*r-py*py));box(name+k,0,y+py,half*2,2,color,parent);}}
// Parent clipping caused pointer tests to miss visible controls outside 1x1 menus.
for(const name of ['HomeScreen','SelectScreen','ResultScreen','CommandScreen'])stretch(find(host,name));
for(const name of ['HomeBackdrop','SelectCanvas','ResultBackdrop','LoadingBackdrop']){const n=find(host,name);if(n)stretch(n);}
home.children=home.children.filter(n=>!/^HomeStripe|^GameSubtitle$|^GameMode$|^StartHelp$/.test(n.name));
const bg=find(home,'HomeBackdrop');bg.imageColor=0xff000000;
const title=find(home,'GameTitle');title.text='原神格斗1.0';title.fontSize=42;title.minimumFontSize=42;title.enableOutline=false;transform(title,0,155,600,92);
const button=find(home,'StartDuel');button.children=[];button.kind='container';button.raycastTarget=false;transform(button,0,-100,330,72);
const hit=add(button,'StartDuelHit',0,-100,330,72,home);hit.kind='cursor';hit.raycastTarget=true;
capsule('StartShadow',342,80,'101521',button,-5);capsule('StartRim',330,72,'9dbae5',button);capsule('StartPlate',324,66,'263f62',button);capsule('StartHighlight',320,62,'547fb4',button,2);
label('StartDuelText','开始对战',0,0,284,52,23,button);
// Existing begin/selection/result/command controls retain their event identities.
const data=JSON.parse(read(out+'/home-portraits.json'));
for(let i=0;i<2;i++){const p=add(group,'HomeBust'+(i+1),i===0?-490:490,-150,1,1,home);save._pixelJobs.push({path:['HomeScreen',p.name],prefix:'HomePx',count:data[i].rows.length});}
let source=save.assets.scripts[0].source;
const marker="local menuMode='home'";assert(source.includes(marker));
source=source.replace(marker,marker+'\nlocal homePortraitData={'+data.map(d=>luaFrame(packFrame(d))).join(',')+'}\nlocal homePortraitNodes={{},{}}\nresourceGate.showHome=function()return menuMode==\'home\'end');
source=source.replace("menuBind('StartDuel',function()menuMode='select';", "menuBind('StartDuel',function()menuMode='select';resourceGate.request('menu',roleChoice);");
source=source.replace("menuBind('StartDuel',", "menuBind('StartDuelHit',");
source=source.replace("local function menuInit()", "local function menuInit()");
source=source.replace("local menuMode='home'", "uiParents.StartDuelHit='HomeScreen'\nlocal menuMode='home'");
source=source.replace("{'GameTitle','StartDuel'}", "{'GameTitle','StartDuel','StartDuelHit'}");
source=source.replace('portraitNodes={};portraitRole={};gridNodes={};gridRoles={};menuDirty=true','portraitNodes={};portraitRole={};gridNodes={};gridRoles={};homePortraitNodes={{},{}};menuDirty=true');
const shown="rootNode('HomeScreen'):SetVisible(menuMode=='home');";assert(source.includes(shown));
source=source.replace(shown,shown+"if menuMode=='home'then local cw,ch=game.GetUICanvasSize();local hs=math.min(1,cw/1600,ch/900);for i=1,2 do local bust=rootNode('HomeScreen'):FindChild('HomeBust'..i);bust:SetAnchoredPosition((i==1 and -490 or 490)*hs,-ch/2+300*hs);paintFrame(bust,'HomePx',homePortraitData[i],homePortraitData[i].scale*hs,homePortraitNodes[i])end;for _,name in ipairs({'GameTitle','StartDuel'})do local node=rootNode('HomeScreen'):FindChild(name);node.localScaleX=hs;node.localScaleY=hs;node:SetAnchoredPosition(0,(name=='GameTitle'and 155 or -100)*hs)end end;");
source=source.replace("{'GameTitle','StartDuel'}", "{'GameTitle','StartDuel','StartDuelHit'}");
source=source.replace('local homePortraitData=','homePortraitData=').replace('local homePortraitNodes=','homePortraitNodes=').replace(/\bhomePortraitData\b/g,'resourceGate.homePortraitData').replace(/\bhomePortraitNodes\b/g,'resourceGate.homePortraitNodes');
save.assets.scripts[0].source=source;write(out+'/base.save.json',JSON.stringify(save));
let runtime=read('work/v2-loading-generated.lua','utf8');
runtime=runtime.replace("local desired,seen={},{}","local desired,seen={},{}\n local showHome=mode=='menu'and resourceGate.showHome and resourceGate.showHome()");
runtime=runtime.replace("if mode=='battle'then\n", "if showHome then for _,frame in ipairs(homePortraitData)do want(frame)end end\n if mode=='battle'then\n");
runtime=runtime.replace('else\n  for n=1,10 do want(thumbData', 'elseif not showHome then\n  for n=1,10 do want(thumbData');
runtime=runtime.replace("for _,frames in ipairs({portraitData,thumbData})", "for _,frame in ipairs(homePortraitData)do visit(frame)end\n for _,frames in ipairs({portraitData,thumbData})");
runtime=runtime.replace("if name=='Sprite'then", "if name=='HomeBust1'or name=='HomeBust2'then wanted=showHome and job.count or 0\n  elseif name=='Sprite'then");
runtime=runtime.replace("wanted=mode=='menu'and thumbData[role]", "wanted=mode=='menu'and not showHome and thumbData[role]");
runtime=runtime.replace(/\bhomePortraitData\b/g,'resourceGate.homePortraitData');
write('work/group1-home-loading.lua',runtime);
write(out+'/主界面修订记录.json',JSON.stringify({title:'原神格斗1.0',subtitle:false,background:'full canvas black',portraits:data.map(d=>({grid:[d.w,d.h],rectangles:d.rows.length})),pointerFix:'stretch 1x1 parent menus; preserve event IDs',deviceVerified:false},null,2));
console.log('HOME_RESTYLED',data.map(d=>d.rows.length));

