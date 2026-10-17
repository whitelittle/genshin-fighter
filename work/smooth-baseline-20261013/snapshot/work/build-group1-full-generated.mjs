import{loadGroup1Set}from'./group1-sets.mjs';
import{readFileSync,writeFileSync,mkdirSync,existsSync}from'node:fs';import assert from'node:assert/strict';
import{packFrame,luaFrame}from'./v2-pack.mjs';
const out='outputs/midphase-final/assembly';mkdirSync(out,{recursive:true});
const all=JSON.parse(readFileSync('assets/roster-v2/roster.json')).filter(r=>r[0]!=='ronova'),talents=JSON.parse(readFileSync('assets/roster-v2/talent-index.json'));
const active=new Set([...JSON.parse(readFileSync('outputs/motion-production/batch-plan.json')).samples,...JSON.parse(readFileSync('outputs/motion-production/batch-plan.json')).batches[0].roles].map(r=>r[0]));const roster=all.filter(r=>active.has(r[0]));assert.equal(roster.length,19);
const legacySets=roster.map(([key],i)=>JSON.parse(readFileSync(existsSync(`assets/roster-v2/${key}-frames.json`)?`assets/roster-v2/${key}-frames.json`:`assets/${i<2?'vnext':'test-v1'}/${key}-frames.json`)));
const sets=roster.map(([key],i)=>loadGroup1Set(key,legacySets[i]));

const headsAll=JSON.parse(readFileSync('assets/roster-v2/heads.json')),thumbsAll=JSON.parse(readFileSync('assets/roster-v2/thumbs.json'));
const heads=roster.map(r=>headsAll[all.findIndex(x=>x[0]===r[0])]),thumbs=roster.map(r=>thumbsAll[all.findIndex(x=>x[0]===r[0])]);
let save=JSON.parse(readFileSync('outputs/test-v1/base.save.json')),source=save.assets.scripts[0].source;source=source.replace(/(?:\\\d{3})+/g,s=>Buffer.from(s.match(/\d{3}/g).map(Number)).toString('utf8'));
function rep(a,b){assert.ok(source.includes(a),'missing '+a.slice(0,100));source=source.replace(a,b);}
const packed=[],aliases=[];let rawBytes=0,compressedBytes=0,hexBytes=0,uniqueFrames=0;
const pack=f=>{const p=packFrame(f);rawBytes+=p.rawBytes;compressedBytes+=p.compressedBytes;hexBytes+=f.rows.length*10;uniqueFrames++;return luaFrame(p);};
for(let role=0;role<sets.length;role++){const seen=new Map();packed.push('{'+sets[role].frames.map((f,i)=>{const key=JSON.stringify([f.rows,f.scale,f.anchor]);if(seen.has(key)){aliases.push(`spriteData[${role+1}][${i+1}]=spriteData[${role+1}][${seen.get(key)}]`);return'false';}seen.set(key,i+1);return pack(f);}).join(',')+'}');}
const headPacked=heads.map(pack),thumbPacked=thumbs.map(pack),portraitCap=Math.max(...heads.map(f=>f.rows.length)),thumbCap=Math.max(...thumbs.map(f=>f.rows.length)),maxPool=Math.max(...sets.map(s=>s.pool));
const start=source.indexOf('local spriteData='),end=source.indexOf('local spriteCache=',start);
const px=f=>`{scale=${f.scale},anchor={${f.anchor}},rows={${f.rows.map(([x,y,w,h,r,g,b,a])=>`{${x},${y},${w},${h},${((a<<24)|(r<<16)|(g<<8)|b)>>>0}}`).join(',')}}}`;
source=source.slice(0,start)+readFileSync('work/v2-unpack.lua','utf8')+`\nlocal spriteData={${packed}}\n${aliases.join('\n')}\nlocal poseIds={${sets.map(s=>'{'+s.frames.map((f,i)=>`[${JSON.stringify(f.pose||'idle')}]=${i+1}`).join(',')+'}')}\nlocal phoenixData={${JSON.parse(readFileSync('assets/vnext/phoenix.json')).map(px)}}\nlocal portraitData={${headPacked}}\nlocal thumbData={${thumbPacked}}\nlocal portraitPool=${portraitCap}\nlocal roleNames={${roster.map(r=>JSON.stringify(r[1]))}}\nlocal poolCaps={${sets.map(s=>s.pool)}}\nlocal resourceGate={busy=true,mode='menu',caps={0,0},request=nil}\n`+source.slice(end);
source=source.replace('\nlocal phoenixData','}\nlocal phoenixData');
rep("local data=resourceGate.mode=='menu' and previewData[a.role] or spriteData[a.role][pose]",'local data=spriteData[a.role][pose]\n if resourceGate.mode~=\'battle\'or not data or not data.rows then return end');
{
 const begin=source.indexOf('local count=#data.rows'),end=source.indexOf('  visualCounts[i]=count',begin);
 assert.ok(begin>=0&&end>begin);
 source=source.slice(0,begin)+`local count=data.count;local previous=visualCounts[i]or resourceGate.caps[i]
  for n=1,math.max(count,previous)do
   local node=nodes[n];if not node then node=pool:FindChild('P'..n);nodes[n]=node end
   local v=values[n];if not v then v={};values[n]=v end
   local visible=n<=count
   if v.visible~=visible then node:SetVisible(visible);v.visible=visible;visualWrites=visualWrites+1 end
   if visible then
    local px,py,pw,ph,color=framePixel(data,n)
    local x=(px+pw/2-data.anchor[1])*data.scale;local y=(data.anchor[2]-py-ph/2)*data.scale;local w,h=pw*data.scale,ph*data.scale
    if v.x~=x or v.y~=y then node:SetAnchoredPosition(x,y);v.x=x;v.y=y;visualWrites=visualWrites+1 end
    if v.w~=w or v.h~=h then node:SetSizeDelta(w,h);v.w=w;v.h=h;visualWrites=visualWrites+1 end
    if v.color~=color then node.imageColor=color;v.color=color;visualWrites=visualWrites+1 end
   end
  end
`+source.slice(end);
}
rep('local function resetRound()','local roundWinner=0\nlocal function resetRound()');rep('if winner>0 then wins[winner]=wins[winner]+1 end','roundWinner=winner\n if winner>0 then wins[winner]=wins[winner]+1 end');
rep('if intermission<=0 then round=round+1;resetRound()end','if intermission<=0 then phase=\'roundLoad\'end');
rep('local function step()','local function step()\n if phase==\'roundLoad\'then return end');
rep('roundIntro=roundIntro})','roundIntro=roundIntro,roundWinner=roundWinner})');rep('roundIntro=s.roundIntro','roundIntro=s.roundIntro;roundWinner=s.roundWinner or 0');
const classes={yaemiko:'trap',kirara:'shielddash',kamisatoayaka:'launch',kamisatoayato:'stance',aratakiitto:'bruiser',sangonomiyakokomi:'heal',tighnari:'mark',cyno:'dash',wanderer:'air',nilou:'wave',faruzan:'launchrange',layla:'shield',neuvillette:'beam',wriothesley:'selfbuff',clorinde:'stance',navia:'shotgun',mualani:'rush',kinich:'grapple',kachina:'shielddash',ineffa:'shieldrange',skirk:'dash',flins:'stance',varka:'bruiser',nicole:'shieldrange',venti:'vortex',zhongli:'shield',furina:'selfbuff',nahida:'mark',mavuika:'rush',raidenshogun:'stance',columbina:'wave',tartaglia:'stance',sandrone:'shieldrange',arlecchino:'debt'};
const designs=[];
let extra='local roleClass={}\n';
roster.forEach(([key,name],j)=>{if(j<11)return;const role=j+1,cls=classes[key]||'wave',t=talents.find(t=>t.key===key),range=['beam','launchrange','shieldrange','mark','trap','wave','vortex'].includes(cls)?340:cls==='shotgun'?245:180,speed=['rush','dash','grapple','air'].includes(cls)?255:['shield','bruiser'].includes(cls)?180:225,damage=cls==='bruiser'?22:cls==='shield'||cls==='heal'?12:17,dash=cls==='rush'?850:cls==='grapple'?650:cls==='dash'?500:cls==='shielddash'?350:0;
 extra+=`roleClass[${role}]='${cls}'\nspecs[${role}]={speed=${speed},light={startup=8,active=4,recovery=16,range=${Math.min(180,range-50)},damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=135,damage=8,stun=20,push=22,height='low'},heavy={startup=${cls==='bruiser'?25:21},active=5,recovery=28,range=${cls==='beam'?385:190},damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=${cls==='beam'?20:14},active=6,recovery=28,range=${range},damage=${damage},stun=30,push=40${dash?',dash='+dash:''}},super={startup=24,active=10,recovery=42,range=${range+110},heightRange=230,damage=40,stun=42,push=65}}\nmoveNames[${role}]={light='普通攻击',low='下段攻击',heavy='重击',rising='升空攻击',overhead='上段攻击',special=${JSON.stringify(t?.E||'元素特殊技')},super=${JSON.stringify(t?.Q||'元素必杀')}}\n`;
 designs.push({role,key,name,class:cls,E:t?.E,Q:t?.Q,reference:t?.url,visual:'12 key poses + 8 aliases',adaptation:'E/Q simplified to fighter timing; Q single hit. Not full original RPG mechanics.'});});
rep('local function recordDirection()',extra+'\nlocal function recordDirection()');
rep('local base=s.damage',`local base=s.damage\n local cls=roleClass[a.role]\n if(a.stanceLife or 0)>0 then base=base+3 end\n if cls=='shotgun'and atk.kind=='special'then base=base+(a.charges or 0)*2;a.charges=0 end\n if cls=='trap'and atk.kind=='super'then base=base+(a.totems or 0)*4;a.totems=0 end\n if cls=='debt'and atk.kind=='heavy'and(b.debt or 0)>0 then base=base+7;b.debt=0 end\n if cls=='mark'and atk.kind=='heavy'and(b.marked or 0)>0 then base=base+5;b.marked=0 end`);
rep('if b.role==11 and(b.armorLife or 0)>0 then',"if(b.role==11 or roleClass[b.role]=='shield'or roleClass[b.role]=='shielddash'or roleClass[b.role]=='shieldrange')and(b.armorLife or 0)>0 then");
rep("if a.role==3 and not blocked and atk.kind=='special'then b.chill=90 end",`if a.role==3 and not blocked and atk.kind=='special'then b.chill=90 end
 if cls=='shotgun'and not blocked and atk.kind=='light'then a.charges=math.min(3,(a.charges or 0)+1)end
 if cls=='mark'and not blocked and atk.kind=='special'then b.marked=180 end
 if cls=='debt'and not blocked and atk.kind=='special'then b.debt=180 end
 if cls=='vortex'and not blocked and atk.kind=='super'then b.x=clamp(a.x+a.face*90,-535,535)end
 if cls=='heal'and atk.kind=='super'then a.hp=math.min(100,a.hp+12)end
 if cls=='debt'and atk.kind=='super'then a.hp=math.min(100,a.hp+10)end`);
rep("(atk.kind=='rising'or(a.role==4 and atk.kind=='special'))", "(atk.kind=='rising'or((a.role==4 or roleClass[a.role]=='launch'or roleClass[a.role]=='launchrange')and atk.kind=='special')or((roleClass[a.role]=='bruiser'or roleClass[a.role]=='selfbuff')and atk.kind=='super'))");
rep('a.chill=math.max(0,(a.chill or 0)-1);',`a.stanceLife=math.max(0,(a.stanceLife or 0)-1);a.marked=math.max(0,(a.marked or 0)-1);a.debt=math.max(0,(a.debt or 0)-1)
 a.chill=math.max(0,(a.chill or 0)-1);`);
rep("if atk.t==atk.startup then",`if atk.t==atk.startup then
   local cls=roleClass[a.role]
   if atk.kind=='special'then
    if cls=='shield'or cls=='shielddash'or cls=='shieldrange'then a.armorLife=180 end
    if cls=='stance'or cls=='bruiser'or cls=='air'then a.stanceLife=300 end
    if cls=='selfbuff'then a.hp=math.max(1,a.hp-6);a.stanceLife=300 end
    if cls=='heal'then a.hp=math.min(100,a.hp+6)end
    if cls=='trap'then a.totems=math.min(3,(a.totems or 0)+1)end
    if cls=='air'then a.vy=260 end
   end`);
// Menu protocol is a versioned eleven-integer team snapshot.
let a=source.indexOf('-- Preparation snapshots:'),b=source.indexOf('local oldInit=OnInit',a);assert.ok(a>=0&&b>a);source=source.slice(0,a)+readFileSync('work/v2-menu.lua','utf8').replaceAll('__ROLE_COUNT__',String(roster.length))+source.slice(b);
rep("onlineReady=true;menuMode='battle';restart();acc=0", "onlineReady=true;menuMode='battle';startNetworkRound();acc=0");
rep("bind('KeyboardCraftspersonKey15Down',function()commandOpen=not commandOpen end)","bind('KeyboardCraftspersonKey15Down',function()commandOpen=not commandOpen;menuDirty=true end)");
rep("draw()\n stats.text=", "draw()\n if lastDrawPhase~=phase or lastDrawRound~=round or lastDrawScore~=wins[1]*3+wins[2]then menuDirty=true;lastDrawPhase=phase;lastDrawRound=round;lastDrawScore=wins[1]*3+wins[2]end\n rootNode('RoundBanner'):SetVisible(phase=='intro');rootNode('RoundBanner').text=roundIntro<=25 and'FIGHT'or({'ROUND 1','ROUND 2','ROUND 3'})[math.min(round,3)]\n stats.text=");
rep('local resendTime=0','local lastDrawPhase,lastDrawRound,lastDrawScore\nlocal resendTime=0');
const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean),host=find(save.assets.server.root,'FighterDemo');
const proto={image:structuredClone(find(host,'Hp1')),text:structuredClone(find(host,'Status')),button:structuredClone(find(host,'Light')),group:structuredClone(find(host,'Art'))};let serial=0;
function add(kind,name,x,y,w,h,parent=host){const n=structuredClone(proto[kind]);n.id='r2_'+(++serial);n.name=name;n.children=[];n.active=true;n.visible=true;n.raycastTarget=kind==='button';if(kind==='button')n.kind='cursor';delete n.scriptMappingIds;for(const t of Object.values(n.transformByPlatform)){t.offset={x,y};t.size={x:w,y:h};t.scale={x:1,y:1,z:1};t.rotation={x:0,y:0,z:0};t.anchorMin=t.anchorMax=t.pivot={x:.5,y:.5};}parent.children.unshift(n);return n;}
function box(name,x,y,w,h,color,parent){let n=add('image',name,x,y,w,h,parent);n.imageColor=Number('0xff'+color)>>>0;return n;}
function text(name,str,x,y,w=400,size=20,parent){let n=add('text',name,x,y,w,40,parent);n.text=str;n.fontSize=size;return n;}
// Six native images make one rounded plate; no raster border atlas or extra animation pool.
function rounded(name,x,y,w,h,color,parent,r=12){r=Math.min(r,w/2,h/2);const plate=box(name,x,y,w,h-2*r,color,parent);box(name+'Middle',x,y,w-2*r,h,color,parent);for(const sx of[-1,1])for(const sy of[-1,1]){const c=box(name+'Corner'+sx+'_'+sy,x+sx*(w/2-r),y+sy*(h/2-r),2*r,2*r,color,parent);c.imageId=100002;}return plate;}
function btn(name,str,x,y,w,h,parent){let n=add('button',name,x,y,w,h,parent);const r=Math.min(16,h/2);rounded(name+'Rim',0,0,w,h,'948568',n,r);rounded(name+'Plate',0,0,w-4,h-4,'293446',n,Math.max(1,r-2));text(name+'Caption',str,0,0,w-12,17,n);return n;}
const menu=find(host,'SelectScreen');menu.children=[];
box('SelectCanvas',0,0,1280,740,'141b2b',menu);box('TopGold',0,301,1050,2,'c8ad75',menu);box('BottomGold',0,-342,1050,2,'77664e',menu);
text('RosterTitle','阵 容 选 定',0,327,650,30,menu);text('SelectionHint','按出战顺序选定三个角色',0,-261,900,14,menu);
// Restrained celestial ornament, authored native controls rather than another large bitmap pool.
for(let side of[-1,1]){for(let n=0;n<4;n++){let ornament=box('RosterOrnament'+side+'_'+n,side*(588+n*8),130-n*15,2,340-n*40,'29384d',menu);for(const t of Object.values(ornament.transformByPlatform))t.rotation.z=side*11;}}
let diamond=box('VersusDiamond',0,163,30,30,'9c8358',menu);for(const t of Object.values(diamond.transformByPlatform))t.rotation.z=45;text('VersusGlyph','VS',0,163,70,16,menu);
for(let i=1;i<=2;i++){const x=i===1?-165:165,color=i===1?'477baf':'b14f60';rounded('PreviewRim'+i,x,153,292,268,'877558',menu,24);rounded('PreviewPanel'+i,x,153,288,264,'202a3b',menu,22);rounded('PreviewAccent'+i,x,280,244,4,color,menu,2);for(let side of[-1,1]){box('PreviewBracket'+i+side,x+side*136,160,2,180,'697080',menu);box('PreviewFoot'+i+side,x+side*126,40,24,2,'b09a70',menu);}text('PlayerLabel'+i,'PLAYER '+i,x,258,260,20,menu);text('SelectName'+i,'选定角色后展示',x,45,270,22,menu);text('SelectReady'+i,'ROUND 1 → ROUND 2 → ROUND 3',x,5,320,14,menu);
 for(let n=1;n<=3;n++){const slot=btn('TeamSlot'+i+n,'',i===1?-455:455,231-(n-1)*89,225,77,menu);text('TeamRound'+i+n,'ROUND '+n,-62,0,94,14,slot);text('TeamName'+i+n,'待选角色',48,0,118,14,slot);}}
const jobs=[];
for(let i=1;i<=2;i++){const actor=find(host,i===1?'Keqing':'Diluc'),sprite=find(actor,'Sprite');sprite.children=[];jobs.push({path:[actor.name,'Art','Sprite'],prefix:'P',count:maxPool});const fx=find(actor,'Phoenix');const count=fx.children.filter(n=>n.kind==='image').length;fx.children=[];jobs.push({path:[actor.name,'Phoenix'],prefix:'F',count});const face=find(host,'Portrait'+i);face.children=[];jobs.push({path:[face.name],prefix:'FacePx',count:portraitCap});}
for(let n=1;n<=10;n++){const x=((n-1)%5-2)*112,y=-82-Math.floor((n-1)/5)*94,card=add('button','GridCard'+n,x,y,98,84,menu);rounded('GridPlate'+n,0,0,98,84,'40434b',card,14);box('GridBlue'+n,-44,0,4,56,'62a5e5',card);box('GridRed'+n,44,0,4,56,'ea7986',card);const face=add('group','GridFace'+n,0,0,1,1,card);jobs.push({path:['SelectScreen',card.name,face.name],prefix:'IconPx',count:thumbCap});}
btn('PagePrev','‹',-351,-129,60,65,menu);btn('PageNext','›',351,-129,60,65,menu);let pageLabel=text('PageLabel','',0,-238,500,15,menu);for(const t of Object.values(pageLabel.transformByPlatform))t.size.y=24;
const ready=btn('ReadyConfirm','',150,-310,275,48,menu);ready.children=ready.children.filter(n=>!n.name.endsWith('Caption'));text('ReadyConfirmText','请选满三人',0,0,250,18,ready);btn('BackHome','返回',-185,-310,180,48,menu);
// Restyle existing native action plates as well; preserve their cursor names and hit areas.
function soften(n){for(const c of [...(n.children||[])])soften(c);for(const c of [...(n.children||[])])if(c.kind==='image'&&c.name.endsWith('Plate')&&!n.children.some(k=>k.name===c.name+'Middle')){const t=Object.values(c.transformByPlatform)[0];n.children=n.children.filter(k=>k!==c);rounded(c.name,t.offset.x,t.offset.y,t.size.x,t.size.y,(c.imageColor>>>0).toString(16).slice(-6),n,14);}}
soften(host);
// Register exact direct parents for all named descendants used by the Lua UI cache.
const parents={};function visit(n,parent){if(parent&&parent!==host)parents[n.name]=parent.name;for(const c of n.children||[])visit(c,n);}visit(host,null);
rep('local uiParents={','local uiParents={'+Object.entries(parents).filter(([n])=>n.startsWith('Grid')||n.startsWith('Team')||['RosterTitle','PagePrev','PageNext','PageLabel','SelectName1','SelectName2','SelectReady1','SelectReady2','SelectionHint','ReadyConfirm','ReadyConfirmText','BackHome'].includes(n)).map(([n,p])=>`[${JSON.stringify(n)}]=${JSON.stringify(p)}`).join(',')+',');
// Keep compatibility lookups for now-hidden old stage buttons without displaying them.
for(let i=1;i<=3;i++)btn('SelectStage'+i,'',0,0,1,1,menu).visible=false;
find(host,'BackdropArt').children=[];
for(let s=1;s<=3;s++){const p=find(host,'Stage'+s);p.children=[];
 box('Sky',0,80,1280,600,['82b4c0','8aadc0','839ea9'][s-1],p);box('Hills',0,-3,1280,230,['66887b','7d918a','728981'][s-1],p);
 for(let k=0;k<8;k++){let n=box('Hill'+k,-600+k*178,60+(k%3)*28,250,160,['75968a','78939a','66827e'][s-1],p);n.imageId=100002;}
 if(s===1){
  box('WindriseTrunk',60,2,62,305,'6c5b43',p);for(let k=0;k<8;k++){let n=box('GreatTreeBranch'+k,60+Math.cos(k)*80,75+Math.sin(k)*50,15,175,'6c5b43',p);for(const t of Object.values(n.transformByPlatform))t.rotation.z=k*25-60;}
  for(let k=0;k<15;k++){let n=box('GreatTreeCrown'+k,60+Math.cos(k*2.4)*(110+(k%3)*36),177+Math.sin(k*2.4)*57,215,130,['355e48','456f51','5c8459','789762'][k%4],p);n.imageId=100002;}
  box('StatuePlinth',-305,-83,58,23,'a8b7b3',p);box('StatueColumn',-305,-27,28,100,'bed0ce',p);let n=box('AnemoStatueHead',-305,36,19,19,'d2dfd5',p);n.imageId=100002;box('StatueWings',-305,10,63,8,'cbdcd4',p);
 }else if(s===2){
  box('CityWall',0,30,1280,180,'a2aaa0',p);for(let k=0;k<26;k++)box('CityCrenel'+k,-625+k*50,128,30,25,'aab3a5',p);
  box('GateShadow',65,-24,125,126,'415b63',p);let arch=box('GateArch',65,39,125,125,'415b63',p);arch.imageId=100002;
  for(const x of[-35,165]){box('GateTower'+x,x,54,63,216,'bac3b5',p);box('GateCap'+x,x,169,80,25,'a2b4a3',p);for(let k=0;k<3;k++)box('GateSlit'+x+k,x-20+k*20,101,5,19,'546e76',p);}
  box('Cathedral',-348,160,185,90,'bcc8be',p);for(const x of[-402,-290]){box('CathedralTower'+x,x,207,37,137,'d0d7c5',p);box('CathedralSpire'+x,x,288,24,51,'456879',p);for(const t of Object.values(find(p,'CathedralSpire'+x).transformByPlatform))t.rotation.z=18;}
  for(let k=0;k<17;k++){box('BridgePost'+k,-630+k*78,-95,9,60,'c4c7b7',p);}box('BridgeRail',0,-67,1280,7,'dfddc4',p);
 }else{
  box('StormterrorTower',45,107,133,302,'84928c',p);for(let j=0;j<5;j++)box('CentralTowerBelt'+j,45,-19+j*60,153,12,'a1aaa0',p);
  for(const x of[-14,104]){box('CentralTowerSide'+x,x,119,20,328,'a6b0a2',p);}box('CentralTowerCrown',45,283,178,23,'b2b9a7',p);
  for(let k=0;k<8;k++){const x=-595+k*172;box('BrokenPillar'+k,x,-3,27,212-k%3*32,'a1aca0',p);box('BrokenCapital'+k,x,105-k%3*16,50,15,'bac1ab',p);}
  for(let k=0;k<12;k++){let n=box('AncientRing'+k,45+Math.cos(k*Math.PI/6)*320,131+Math.sin(k*Math.PI/6)*92,150,11,'adb8ad',p);for(const t of Object.values(n.transformByPlatform))t.rotation.z=Math.sin(k*Math.PI/6)*24;}
 }
 box('GroundTop',0,-204,1280,105,['849583','a5ab9b','939d8e'][s-1],p);box('GroundRear',0,-152,1280,4,'d0d5bf',p);box('GroundFront',0,-266,1280,20,'485c57',p);box('GroundLip',0,-254,1280,4,'c5cfb5',p);
 for(let r=0;r<3;r++)box('PavingRow'+r,0,-178-r*29,1280,1,'607870',p);for(let k=0;k<18;k++){let n=box('PavingLine'+k,-680+k*82,-204,1,105,'607870',p);for(const t of Object.values(n.transformByPlatform))t.rotation.z=(k-8.5)*1.9;}
}
save.assets.scripts[0].source=source;save.meta.name='原神格斗 · 三人顺序出战';save._pixelJobs=jobs;
find(host,'Hp1').imageColor=0xff91bce4;find(host,'Hp2').imageColor=0xffe696a5;
save.serverLogic.rules=save.serverLogic.rules.filter(r=>r.signalName!=='FighterSelect');save.serverLogic.rules.push({id:'team-v2',signalName:'FighterTeam',actions:[{kind:'sendClientScriptSignal',target:'AllPlayers',signalName:'FighterTeamOut',params:Array.from({length:11},(_,i)=>({fromSignalParam:i}))}]});
writeFileSync(out+'/base.save.json',JSON.stringify(save));writeFileSync(out+'/roster.json',JSON.stringify(roster,null,2));writeFileSync(out+'/role-designs.json',JSON.stringify(designs,null,2));
writeFileSync(out+'/storage-report.json',JSON.stringify({roster:roster.length,uniqueFrames,rawTupleBytes:rawBytes,oldHexCharacters:hexBytes,compressedBinaryBytes:compressedBytes,compressedBase64Characters:Math.ceil(compressedBytes/3)*4,hexReduction:1-Math.ceil(compressedBytes/3)*4/hexBytes,expandedStorage:'5-byte binary string per rectangle; no retained per-row Lua tables',poolDefinitions:'prefix + count recipes; no repeated placeholder controls',aliasFrames:aliases.length,headsPreserveFullIcon:true,portraitCap,thumbCap,battleCaps:sets.map(s=>s.pool),menuInitialImages:thumbs.slice(0,10).reduce((a,f)=>a+f.rows.length,0),deviceVerified:false},null,2));
console.log('BASE_V2',roster.length,'roles, compressed',compressedBytes,'bytes');
