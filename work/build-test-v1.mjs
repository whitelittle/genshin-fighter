import{readFileSync,writeFileSync,mkdirSync,existsSync}from'node:fs';
import{createRequire}from'node:module';
import{sample,colorProcess,fit}from'file:///C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/static-material-tool/engine.mjs';
const require=createRequire('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/package.json');
const{createCanvas}=require('@napi-rs/canvas');
const out='outputs/test-v1';mkdirSync(out,{recursive:true});
const roster=[['keqing','刻晴','雷楔 / 星斗归位','天街巡游',235,16,145],['diluc','迪卢克','逆焰之刃 · 三段','黎明',180,22,240],['kaeya','凯亚','霜袭','凛冽轮舞',220,14,230],['jean','琴','风压剑','蒲公英之风',215,15,200],['klee','可莉','蹦蹦炸弹','轰轰火花',185,16,290],['lisa','丽莎','苍雷','蔷薇的雷光',190,17,300],['ganyu','甘雨','山泽麟迹','降众天华',205,14,340],['yanfei','烟绯','丹书立约','凭此结契',200,16,270],['xiao','魈','风轮两立','靖妖傩舞',250,17,210],['hutao','胡桃','蝶引来生','安神秘法',230,18,190],['lawachurl','岩盔丘丘王','岩躯冲撞','山崩震地',150,24,240]];
const roles=roster.filter(([key],i)=>i<2||existsSync(`assets/test-v1/${key}-frames.json`));
const sets=roles.map(([k],i)=>JSON.parse(readFileSync(`assets/${i<2?'vnext':'test-v1'}/${k}-frames.json`)));
function small(f,h){const w=Math.max(1,Math.round(f.w*h/f.h)),c=createCanvas(f.w,f.h),ctx=c.getContext('2d');for(const[x,y,rw,rh,r,g,b,a]of f.rows){ctx.fillStyle=`rgba(${r},${g},${b},${a/255})`;ctx.fillRect(x,y,rw,rh);}const raw=sample(ctx.getImageData(0,0,f.w,f.h).data,f.w,f.h,w,h,'average',180),data=colorProcess(raw,new Uint8Array(w*h),{colors:14,tolerance:8}).data;return{w,h,scale:240/h,anchor:[f.anchor[0]*w/f.w,f.anchor[1]*h/f.h],rows:fit(data,w,h).rows};}
const previews=sets.map((s,i)=>small(s.frames.find(f=>!f.pose||f.pose==='idle'),i===10?48:56));
for(const f of previews)for(const r of f.rows){for(let c=4;c<7;c++)r[c]=Math.min(255,Math.round(r[c]*1.1+10));}
const oldPortraits=JSON.parse(readFileSync('assets/vnext/portraits.json'));
const portraits=roles.map(([key],i)=>{const f=i<2?oldPortraits[key]:JSON.parse(readFileSync(`assets/test-v1/${key}-portrait.json`));const p=small(f,18);p.scale=3;p.anchor=[p.w/2,p.h/2];return p;});
const poolMax=Math.max(...sets.map(s=>s.pool)),previewMax=Math.max(...previews.map(f=>f.rows.length)),portraitMax=Math.max(...portraits.map(f=>f.rows.length));
const luaFrame=f=>`{scale=${f.scale},anchor={${f.anchor}},rows={${f.rows.map(([x,y,w,h,r,g,b,a])=>`{${x},${y},${w},${h},${((a<<24)|(r<<16)|(g<<8)|b)>>>0}}`).join(',')}}}`;
const packedFrame=f=>{const palette=[],index=new Map();const hex=n=>{if(n<0||n>255||n!==Math.floor(n))throw Error('packed range '+n);return n.toString(16).padStart(2,'0');};const pixels=f.rows.map(([x,y,w,h,r,g,b,a])=>{const color=((a<<24)|(r<<16)|(g<<8)|b)>>>0;if(!index.has(color)){palette.push(color);index.set(color,palette.length);}return[x,y,w,h,index.get(color)].map(hex).join('');}).join('');return`{scale=${f.scale},anchor={${f.anchor}},palette={${palette}},pixels='${pixels}',count=${f.rows.length}}`;};
const spriteAliases=[];const packedSets=sets.map((s,r)=>{const seen=new Map();return'{'+s.frames.map((f,i)=>{const key=JSON.stringify([f.rows,f.scale,f.anchor]);if(seen.has(key)){spriteAliases.push(`spriteData[${r+1}][${i+1}]=spriteData[${r+1}][${seen.get(key)}]`);return'false';}seen.set(key,i+1);return packedFrame(f);}).join(',')+'}';});
let save=JSON.parse(readFileSync('outputs/duel-vnext/fighter.save.json')),source=save.assets.scripts[0].source;
// Decode only UTF-8 byte escape sequences so the patches stay readable; re-encode on export.
source=source.replace(/(?:\\\d{3})+/g,s=>Buffer.from(s.match(/\d{3}/g).map(Number)).toString('utf8'));
function rep(a,b){if(!source.includes(a))throw Error('missing '+a.slice(0,90));source=source.replace(a,b);}
let begin=source.indexOf('local spriteData='),end=source.indexOf('local spriteCache=',begin);
source=source.slice(0,begin)+`local spriteData={${packedSets.join(',')}}\n${spriteAliases.join('\n')}\nlocal poseIds={${sets.map(s=>'{'+s.frames.map((f,i)=>`[${JSON.stringify(f.pose||'idle')}]=${i+1}`).join(',')+'}').join(',')}}\nlocal phoenixData={${JSON.parse(readFileSync('assets/vnext/phoenix.json')).map(luaFrame).join(',')}}\nlocal portraitData={${portraits.map(luaFrame).join(',')}}\nlocal previewData={${previews.map(luaFrame).join(',')}}\nlocal portraitPool=${portraitMax}\nlocal roleNames={${roles.map(r=>JSON.stringify(r[1])).join(',')}}\nlocal poolCaps={${sets.map(s=>s.pool)}}\nlocal resourceGate={busy=true,mode='menu',caps={${previewMax},${previewMax}},request=nil}\n`+source.slice(end);
rep("local roles={'刻晴','迪卢克'};",'local roles=roleNames;');
source=source.replaceAll("({'刻晴','迪卢克'})",'(roleNames)');
rep('local names={\'刻晴\',\'迪卢克\'}','local names=roleNames');
rep("local uiParents={", "local uiParents={CommandTitle='CommandScreen',CommandBody='CommandScreen',CommandClose='CommandScreen',"+roles.map((r,i)=>`ChooseRole${i+1}='SelectScreen'`).join(',')+",");
rep('local data=spriteData[a.role][pose]',"local data=resourceGate.mode=='menu' and previewData[a.role] or spriteData[a.role][pose]");
rep('local count=#data.rows;local previous=visualCounts[i] or 2335','local count=#data.rows;local previous=visualCounts[i] or resourceGate.caps[i]');
rep("if kind=='special' and a.role==1", "if kind=='special' and a.role==1");
// Extra fighters share deterministic combat rules, with per-role timing/range and E/Q identities.
const extra=roles.slice(2).map((r,j)=>`specs[${j+3}]={speed=${r[4]},light={startup=${8+j%4},active=4,recovery=16,range=${r[6]-65},damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=${r[6]-50},damage=8,stun=20,push=22,height='low'},heavy={startup=22,active=5,recovery=28,range=${r[6]-20},damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=${14+j%5*2},active=6,recovery=28,range=${r[6]},damage=${r[5]},stun=30,push=40${r[0]==='xiao'?',dash=650':r[0]==='hutao'?',dash=380':''}},super={startup=24,active=10,recovery=42,range=${r[6]+130},heightRange=230,damage=40,stun=42,push=65}}\nmoveNames[${j+3}]={light='普通攻击',low='下段攻击',heavy='重击',rising='升空攻击',overhead='上段攻击',special=${JSON.stringify(r[2])},super=${JSON.stringify(r[3])}}`).join('\n');
rep('local function recordDirection()',extra+'\nlocal function recordDirection()');
rep("if (a.face==1 and c.right) or (a.face==-1 and c.left) then kind='overhead' end", "if c.down then kind='rising'elseif(a.face==1 and c.right)or(a.face==-1 and c.left)then kind='overhead'end");
rep("if kind=='super' then a.meter=a.meter-100;", `if kind=='special' and a.role==9 and (a.eCharges or 2)<=0 then return false end
 if kind=='special' and a.role==10 and (a.buffLife or 0)>0 then return false end
 if kind=='special' and a.role==9 then a.eCharges=(a.eCharges or 2)-1;a.eRecharge=240 end
 if kind=='super' then a.meter=a.meter-100;`);
rep('a.attack={kind=kind,t=0,hit=false,connected=false,startup=startup};',`if a.role==7 and kind=='special' then a.x=clamp(a.x-a.face*85,-535,535)end
 a.attack={kind=kind,t=0,hit=false,connected=false,startup=startup};`);
rep("if a.role==1 and atk.kind=='special' then return end", "if (a.role==1 or a.role==10)and atk.kind=='special'then return end");
rep('local damage=blocked and math.max(1,math.floor(s.damage*.15)) or s.damage',`local base=s.damage
 if a.role==8 and(atk.kind=='heavy'or atk.kind=='super')then base=base+(a.seals or 0)*3;a.seals=0 end
 if a.role==10 and(a.buffLife or 0)>0 then base=base+4 end
 if a.role==6 and atk.kind=='special'then base=base+(b.conductive or 0)*3;b.conductive=0 end
 local damage=blocked and math.max(1,math.floor(base*.15))or base
 if a.role==8 and not blocked and(atk.kind=='light'or atk.kind=='special')then a.seals=atk.kind=='special'and 3 or math.min(3,(a.seals or 0)+1)end
 if a.role==6 and not blocked and atk.kind=='light'then b.conductive=math.min(3,(b.conductive or 0)+1)end
 if b.role==11 and(b.armorLife or 0)>0 then damage=math.max(1,math.floor(damage*.6));b.armorLife=0 end
 if a.role==10 and not blocked and atk.kind=='super'then a.hp=math.min(100,a.hp+12)end
 if a.role==3 and not blocked and atk.kind=='special'then b.chill=90 end`);
rep("elseif not blocked and atk.kind=='rising' then", "elseif not blocked and(atk.kind=='rising'or(a.role==4 and atk.kind=='special'))then");
rep('a.markLife=math.max(0,(a.markLife or 0)-1);',`a.chill=math.max(0,(a.chill or 0)-1);a.buffLife=math.max(0,(a.buffLife or 0)-1);a.armorLife=math.max(0,(a.armorLife or 0)-1)
 if a.role==9 then a.eRecharge=math.max(0,(a.eRecharge or 0)-1);if a.eRecharge==0 and(a.eCharges or 2)<2 then a.eCharges=(a.eCharges or 2)+1;a.eRecharge=240 end end
 a.markLife=math.max(0,(a.markLife or 0)-1);`);
rep('if atk.t>=atk.startup and atk.t<atk.startup+s.active then hit(i,3-i)end',`if atk.t==atk.startup then
   if a.role==10 and atk.kind=='special'then a.hp=math.max(1,a.hp-10);a.buffLife=360 end
   if a.role==4 and atk.kind=='super'then a.hp=math.min(100,a.hp+8)end
   if a.role==9 and atk.kind=='super'then a.buffLife=360 end
   if a.role==11 and atk.kind=='special'then a.armorLife=180 end
  end
  if atk.t>=atk.startup and atk.t<atk.startup+s.active then hit(i,3-i)end`);
rep('move*specs[f[i].role].speed/60','move*specs[f[i].role].speed*((p.chill or 0)>0 and .8 or 1)/60');
rep('then p.vy=465 end',"then p.vy=p.role==9 and(p.buffLife or 0)>0 and 600 or 465 end");
rep('x=i==1 and -50 or 50','x=i==1 and -185 or 185');
// Projectile timing is represented in simulation rather than rendering; no arbitrary UI callback drives hits.
rep("if a.role==2 and atk.kind=='super' then range=", "if a.role==5 or a.role==6 or a.role==7 or a.role==8 then if atk.kind=='special'then range=math.min(range,90+(atk.t-atk.startup)*45)end end\n if a.role==2 and atk.kind=='super' then range=");
rep("pose=a.role==1 and ids.eThrow or ids.e1","pose=ids.eThrow or ids.e1 or ids.special or ids.slash");
rep('local key=a.role*100+pose',"pose=pose or ids.idle\n local key=a.role*100+pose");
// Replace raster backdrop with a crisp native scene. No background pool is instantiated.
begin=source.indexOf(' local data=stageArtData[stage]');end=source.indexOf('\nend',begin);source=source.slice(0,begin)+source.slice(end);
begin=source.indexOf('local stageArtData=');end=source.indexOf('local drawnStage=',begin);source=source.slice(0,begin)+source.slice(end);
// Full menu source has preparation/loading/results synchronization.
begin=source.indexOf('-- Local menu presentation;');end=source.indexOf('local oldInit=OnInit',begin);
source=source.slice(0,begin)+readFileSync('work/test-v1-menu.lua','utf8').replaceAll('__ROLE_COUNT__',roles.length).replaceAll('__COMMAND_ROWS__',roles.map(r=>`[${JSON.stringify(r[1])}]`).join(','))+source.slice(end);
source=source.replace("menuBind('ChooseKeqing'", "menuBind('ChooseRole1'");
rep("or not menuReady[1] or not menuReady[2] then return end","or not menuReady[1] or not menuReady[2] or not menuLoaded[1] or not menuLoaded[2] or resourceGate.busy then return end");
rep("seat==2 and menuReady[1] and menuReady[2] then joinRequest()", "seat==2 and menuReady[1] and menuReady[2] and menuLoaded[1] and menuLoaded[2] and not resourceGate.busy then joinRequest()");
rep('function OnUpdate(dt)\n menuTime=',"function OnUpdate(dt)\n if resourceGate.busy then menuTime=menuTime+dt;return end\n menuTime=");
rep('if handshakeTime>=1 then','if handshakeTime>=1 then\n  retryFlow()');
rep("game.ServerSignal('FighterJoin'):SendSignal()", "local s=game.ServerSignal('FighterJoin');s:AddInt(menuEpoch);s:SendSignal()");
rep("'FighterJoined',function()", "'FighterJoined',function(_,params)\n  if not params or tonumber(params[1])~=menuEpoch then return end");
rep("bind('KeyboardCharacterSkill3KeyDown'", "bind('KeyboardCharacterSkill1KeyDown',function()sendInput('skill')end)\n bind('KeyboardCharacterSkill2KeyDown',function()sendInput('ultimate')end)\n bind('KeyboardCraftspersonKey15Down',function()commandOpen=not commandOpen end)\n bind('KeyboardCharacterSkill3KeyDown'");
const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean),host=find(save.assets.server.root,'FighterDemo');
const proto={image:structuredClone(find(host,'Hp1')),text:structuredClone(find(host,'Status')),button:structuredClone(find(host,'Light')),group:structuredClone(find(host,'Art'))};let serial=0;
function add(kind,name,x,y,w,h,parent=host){const n=structuredClone(proto[kind]);n.id='tv1_'+(++serial);n.name=name;n.children=[];n.active=true;n.visible=true;n.raycastTarget=kind==='button';delete n.scriptMappingIds;for(const t of Object.values(n.transformByPlatform)){t.offset={x,y};t.size={x:w,y:h};t.scale={x:1,y:1,z:1};t.rotation={x:0,y:0,z:0};t.anchorMin=t.anchorMax=t.pivot={x:.5,y:.5};}parent.children.unshift(n);return n;}
function box(name,x,y,w,h,color,parent){const n=add('image',name,x,y,w,h,parent);n.imageColor=Number('0xff'+color)>>>0;return n;}
function text(name,str,x,y,w=400,size=20,parent){const n=add('text',name,x,y,w,44,parent);n.text=str;n.fontSize=size;return n;}
function btn(name,str,x,y,w,h,parent){const n=add('button',name,x,y,w,h,parent);box(name+'Plate',0,0,w,h,'233a50',n);text(name+'Caption',str,0,0,w,18,n);return n;}
// Pools are definitions only; phased loader trims them to the selected fighters.
for(let i=1;i<=2;i++){const actor=find(host,i===1?'Keqing':'Diluc'),p=find(actor,'Sprite');p.children=[];for(let n=1;n<=poolMax;n++){const v=box('P'+n,0,0,1,1,'ffffff',p);v.visible=false;}const face=find(host,'Portrait'+i);face.children=face.children.filter(n=>n.name.startsWith('FaceFrame'));for(let n=1;n<=portraitMax;n++){const v=box('FacePx'+n,0,0,1,1,'ffffff',face);v.visible=false;}}
find(host,'BackdropArt').children=[];
const select=find(host,'SelectScreen');select.children=select.children.filter(n=>!/^Choose(Keqing|Diluc)$/.test(n.name));
for(let i=0;i<roles.length;i++){const x=(i%6-2.5)*176,y=-185-Math.floor(i/6)*74;const b=btn('ChooseRole'+(i+1),roles[i][1],x,y,164,62,select);box('Element'+i,-72,0,4,52,['a389dc','dc7852','8bbbd0','72b599','dc7852','a389dc','8bbbd0','dc7852','72b599','dc7852','ba9a61'][i],b);for(const t of Object.values(b.children.find(n=>n.name.endsWith('Caption')).transformByPlatform)){t.offset.x=20;t.size.x=115;}
 const thumb=small(portraits[i],12);for(let j=0;j<thumb.rows.length;j++){const[rX,rY,w,h,r,g,bl,a]=thumb.rows[j];const n=box('Thumb'+i+'_'+j,-47+(rX+w/2-thumb.w/2)*3,(thumb.h/2-rY-h/2)*3,w*3,h*3,'ffffff',b);n.imageColor=((a<<24)|(r<<16)|(g<<8)|bl)>>>0;}}
for(const name of ['ReadyConfirm','BackHome'])for(const t of Object.values(find(host,name).transformByPlatform))t.offset.y=-324;
find(host,'SelectionHint').text='';for(const t of Object.values(find(host,'SelectionHint').transformByPlatform))t.offset.y=270;
for(let i=1;i<=2;i++){for(const t of Object.values(find(host,'PreviewPanel'+i).transformByPlatform)){t.offset.y=75;t.size.y=330;}for(const t of Object.values(find(host,'SelectReady'+i).transformByPlatform))t.offset.y=-80;}
for(let i=1;i<=3;i++)for(const t of Object.values(find(host,'SelectStage'+i).transformByPlatform))t.offset.y=-128;
// Native scenery: sharp silhouettes, matching perspective paving, no upscaled raster background.
for(let s=1;s<=3;s++){const p=find(host,'Stage'+s);p.children=[];box('Sky',0,105,1280,570,['78a6b4','7396ae','667c96'][s-1],p);box('Horizon',0,-30,1280,180,['6f907c','72808a','687278'][s-1],p);
 for(let k=0;k<13;k++){box('FarHill'+k,-660+k*112,-20,180,100+Math.sin(k*1.7)*50,['66866f','677789','596977'][s-1],p);}
 if(s===1){for(let k=0;k<8;k++){box('Trunk'+k,-610+k*179,0,11,150,'545c47',p);for(let j=0;j<7;j++){const crown=box('Crown'+k+'_'+j,-610+k*179+Math.sin(j*2)*28,82+j*14,104-j*8,68-j*3,['3e6954','4b7658','567e59','719366'][j%4],p);crown.imageShape=100002;}}box('Castle',210,117,110,85,'9da9a0',p);for(let k=0;k<4;k++)box('CastleTower'+k,145+k*44,177,20,78,'afb9aa',p);}
 else if(s===2){box('Bridge',0,-10,1280,22,'b2b3a0',p);for(let k=0;k<15;k++){box('BridgePost'+k,-630+k*90,22,9,78,'c6c5ad',p);}box('Rail',0,61,1280,8,'ddd7b6',p);for(let k=0;k<10;k++){box('House'+k,-600+k*130,132,105,125+(k%3)*21,'929e9c',p);box('Roof'+k,-600+k*130,220+(k%3)*10,124,22,'51677d',p);}}
 else{for(let k=0;k<7;k++){box('Ruin'+k,-595+k*196,42,35,235-k%3*35,'919687',p);box('Capital'+k,-595+k*196,161-k%3*17,57,18,'b6b5a0',p);for(let j=0;j<3;j++)box('RuinGroove'+k+'_'+j,-606+k*196+j*11,42,2,203-k%3*35,'69766f',p);}}
 box('GroundTop',0,-204,1280,105,s===1?'899681':s===2?'a6a69a':'89918a',p);box('RearEdge',0,-152,1280,4,'d0cfb2',p);box('GroundFront',0,-266,1280,20,'495d59',p);box('GroundLip',0,-254,1280,4,'c0c0a9',p);
 for(let r=0;r<3;r++)box('PaveRow'+r,0,-178-r*29,1280,1,'647b73',p);
 for(let k=0;k<18;k++){const line=box('PaveLine'+k,-680+k*82,-204,1,105,'647b73',p);for(const t of Object.values(line.transformByPlatform))t.rotation.z=(k-8.5)*1.9;}
 // First child is foreground in the authoring export.
}
const command=add('group','CommandScreen',0,0,1,1);box('CommandBackdrop',0,0,1000,560,'14273b',command);text('CommandTitle','指令表',0,218,800,32,command);const commandBody=text('CommandBody','',0,5,900,20,command);for(const t of Object.values(commandBody.transformByPlatform))t.size.y=370;btn('CommandClose','关闭 · H',0,-225,170,46,command);
btn('CommandToggle','指令',540,322,75,34);btn('ExitMatch','退出',-540,322,75,34);
const touch=['Light','Heavy','Jump','Block','Skill','Ultimate'];const labels=['轻','重','跳','防','E','Q'];
for(let i=0;i<touch.length;i++){const n=find(host,touch[i]);n.kind='cursor';n.children=[];for(const t of Object.values(n.transformByPlatform)){t.offset={x:345+(i%3)*88,y:-210-Math.floor(i/3)*90};t.size={x:76,y:76};}const surface=box(touch[i]+'Circle',0,0,76,76,i===4?'486c9a':i===5?'926840':'263d53',n);surface.imageShape=100002;text(touch[i]+'Label',labels[i],0,0,70,23,n);}
const stickBase=box('StickBase',-440,-245,166,166,'263f50');stickBase.imageId=100002;stickBase.imageColor=0xb0263f50;
for(let d=1;d<=9;d++){const n=find(host,'Stick'+d);n.kind='cursor';n.children=[];for(const t of Object.values(n.transformByPlatform)){t.offset={x:-440+((d-1)%3-1)*49,y:-245+(Math.floor((d-1)/3)-1)*49};t.size={x:49,y:49};}text('StickGlyph'+d,['↙','↓','↘','←','●','→','↖','↑','↗'][d-1],0,0,46,d===5?22:18,n);}
for(const name of ['Help','MotionHelp'])find(host,name).visible=false;
find(host,'TopPanel').imageColor=0xf018293d;
for(let i=1;i<=2;i++){find(host,'HpBack'+i).imageColor=0xff0d1723;find(host,'Hp'+i).imageColor=i===1?0xffa995e5:0xffee9a65;find(host,'Meter'+i).imageColor=0xffd8bd77;}
const normalize=n=>{if(n.imageShape){n.imageId=n.imageShape;delete n.imageShape;}for(const c of n.children||[])normalize(c);};normalize(host);
save.serverLogic.rules.find(r=>r.id==='join').actions[0].params=[{fromSignalParam:0}];
save.assets.scripts[0].source=source;save.serverLogic.rules.push({id:'flow',signalName:'FighterFlow',actions:[{kind:'sendClientScriptSignal',target:'AllPlayers',signalName:'FighterFlowOut',params:Array.from({length:4},(_,i)=>({fromSignalParam:i}))}]});
writeFileSync(out+'/base.save.json',JSON.stringify(save));writeFileSync(out+'/roster.json',JSON.stringify(roles,null,2));writeFileSync(out+'/resource-budgets.json',JSON.stringify({roles:roles.length,previewPool:previewMax,portraitPool:portraitMax,battleCaps:sets.map(s=>s.pool),bootImages:previewMax*2+portraitMax*2,stageRasterImages:0,deviceVerified:false},null,2));
writeFileSync(out+'/server-logic.json',JSON.stringify(save.serverLogic,null,2));
writeFileSync('work/test-v1-loading-generated.lua',readFileSync('work/test-v1-loading.lua','utf8').replaceAll('PREVIEW_CAP',String(previewMax)));
console.log({out,roles:roles.length,previewMax,portraitMax,poolMax});


