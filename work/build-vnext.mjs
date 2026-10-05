import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {validateServerGiaCompatibility,importGia} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const out=process.env.DUEL_OUT||'outputs/duel-vnext';mkdirSync(out,{recursive:true});
const artDir=process.env.DUEL_ART||'assets/vnext';
const sets=['keqing','diluc'].map(r=>JSON.parse(readFileSync(`${artDir}/${r}-frames.json`)));
const portraits=JSON.parse(readFileSync(`${artDir}/portraits.json`));
const phoenix=JSON.parse(readFileSync(`${artDir}/phoenix.json`));
const stages=JSON.parse(readFileSync(`${artDir}/stages.json`));
const stagePool=Math.max(...stages.map(f=>f.rows.length));
const poolSize=Math.max(...sets.map(s=>s.pool)),fxPool=Math.max(...phoenix.map(s=>s.rows.length));
const portraitPool=Math.max(...Object.values(portraits).map(f=>f.rows.length));
const luaFrame=a=>`{scale=${a.scale},anchor={${a.anchor}},rows={${a.rows.map(([x,y,w,h,r,g,b,alpha])=>`{${x},${y},${w},${h},${((alpha<<24)|(r<<16)|(g<<8)|b)>>>0}}`).join(',')}}}`;
let source=readFileSync('outputs/visual-cache/fighter_online_rollback_debug.lua','utf8');
function rep(a,b){assert.equal(source.split(a).length,2,'replace '+a.slice(0,90));source=source.replace(a,b);}
rep('local function rootNode(name)',`local uiParents={StartDuel='HomeScreen',ChooseKeqing='SelectScreen',ChooseDiluc='SelectScreen',ReadyConfirm='SelectScreen',ReadyConfirmText='ReadyConfirm',BackHome='SelectScreen',SelectName1='SelectScreen',SelectName2='SelectScreen',SelectReady1='SelectScreen',SelectReady2='SelectScreen',SelectionHint='SelectScreen',Rematch='ResultScreen',Reselect='ResultScreen',ResultHome='ResultScreen',ResultTitle='ResultScreen',ResultScore='ResultScreen'}
local function rootNode(name)`);
rep('local node=rootNodes[name];if not node then node=root:FindChild(name);rootNodes[name]=node end;return node',"local node=rootNodes[name];if not node then local parent=root;if uiParents[name]then parent=rootNode(uiParents[name])end;node=parent:FindChild(name);rootNodes[name]=node end;return node");
rep('local stage,roleChoice=1,{1,2}','local stage,roleChoice=1,{1,2}\nlocal roundIntro=90');
const spriteStart=source.indexOf('local spriteData='),spriteEnd=source.indexOf('\nlocal spriteCache=',spriteStart);
assert.ok(spriteEnd>spriteStart);
source=source.slice(0,spriteStart)+'local spriteData={'+sets.map(s=>'{'+s.frames.map(luaFrame).join(',')+'}').join(',')+'}\nlocal poseIds={'+sets.map(s=>'{'+s.frames.map((f,i)=>`[${JSON.stringify(f.pose||'idle')}]=${i+1}`).join(',')+'}').join(',')+'}\nlocal phoenixData={'+phoenix.map(luaFrame).join(',')+'}'+source.slice(spriteEnd);
rep("local function startAttack(i,kind)\n local a=f[i]",`local function startAttack(i,kind)
 local a=f[i]
 if kind=='special' and a.role==1 and (a.markLife or 0)>0 then kind='teleport' end
 if kind=='special' and a.role==2 then
  local current=a.attack
  local stage=((a.eWindow or 0)>0 or current and(current.kind=='special' or current.kind=='e2'))and(a.eStage or 0)+1 or 1
  if stage>3 then return false end
  if stage==2 then kind='e2' elseif stage==3 then kind='e3' end
 end`);
rep('local cancel=canCancel(i,kind)',`local cancel=canCancel(i,kind)
 if a.role==2 and a.attack and(kind=='e2' or kind=='e3')then
  local old=a.attack;local os=specs[2][old.kind]
  cancel=a.stun<=0 and a.down<=0 and old.t>=old.startup+os.active and old.t<=old.startup+os.active+os.recovery
 end`);
rep("a.attack={kind=kind,t=0,hit=false,connected=false,startup=startup};",`if a.role==2 and(kind=='special' or kind=='e2' or kind=='e3')then a.eStage=kind=='special' and 1 or(kind=='e2' and 2 or 3);a.eWindow=45 end
 a.attack={kind=kind,t=0,hit=false,connected=false,startup=startup};`);
rep("specs[2].heavy.height=nil",`specs[2].heavy.height=nil
 specs[1].special={startup=9,active=1,recovery=17,range=0,damage=0,stun=0,push=0}
 specs[1].teleport={startup=10,active=5,recovery=26,range=145,damage=16,stun=28,push=32}
 specs[2].special={startup=18,active=5,recovery=24,range=180,damage=10,stun=32,push=15}
 specs[2].e2={startup=14,active=5,recovery=25,range=190,damage=11,stun=34,push=15}
 specs[2].e3={startup=21,active=6,recovery=33,range=210,damage=18,stun=36,push=40}
 specs[2].super.active=36;specs[2].super.range=570;specs[2].super.heightRange=100
 moveNames[1].special='雷楔';moveNames[1].teleport='星斗归位'
 moveNames[2].special='逆焰之刃·一';moveNames[2].e2='逆焰之刃·二';moveNames[2].e3='逆焰之刃·三'`);
rep("remaining=60;phase='fight';freeze=0;intermission=0;", "remaining=60;phase='intro';roundIntro=90;freeze=0;intermission=0;");
rep("local a,b=f[i],f[j];local atk=a.attack;local s=specs[f[i].role][atk.kind]",`local a,b=f[i],f[j];local atk=a.attack;local s=specs[f[i].role][atk.kind]
 if a.role==1 and atk.kind=='special' then return end`);
rep('if distance<0 or distance>s.range+20 then return end',`local range=s.range
 if a.role==2 and atk.kind=='super' then range=90+math.max(0,atk.t-atk.startup)*14 end
 if distance<0 or distance>range+20 then return end`);
rep("if s.height=='high' and b.crouch then blocked=false end","if (s.height=='high' or a.y>20) and b.crouch then blocked=false end");
rep("(atk.kind=='heavy' or atk.kind=='overhead' or atk.kind=='super' or atk.kind=='special')", "(atk.kind=='heavy' or atk.kind=='overhead' or atk.kind=='super' or atk.kind=='teleport' or atk.kind=='e3')");
rep(' local a=f[i]\n if a.stun>0 then',` local a=f[i]
 a.markLife=math.max(0,(a.markLife or 0)-1);a.eWindow=math.max(0,(a.eWindow or 0)-1)
 if a.stun>0 then a.eWindow=0 end
 if a.stun>0 then`);
rep('local atk=a.attack;local s=specs[f[i].role][atk.kind];atk.t=atk.t+1',`local atk=a.attack;local s=specs[f[i].role][atk.kind];atk.t=atk.t+1
  if a.role==1 and atk.kind=='special' and atk.t==atk.startup then
   local distance=(f[3-i].x-a.x)*a.face;a.markX=clamp(a.x+a.face*clamp(distance-50,80,230),-535,535);a.markLife=180
  elseif atk.kind=='teleport' and atk.t==atk.startup then a.x=a.markX or a.x;a.markLife=0 end
  if a.role==2 and(atk.kind=='special' or atk.kind=='e2' or atk.kind=='e3')then a.eWindow=45 end`);
rep(" tick=tick+1\n if phase~='fight' then",` tick=tick+1
 if phase=='intro' then roundIntro=roundIntro-1;if roundIntro<=0 then phase='fight' end;return end
 if phase~='fight' then`);
rep('stage=stage,roleChoice=roleChoice})','stage=stage,roleChoice=roleChoice,roundIntro=roundIntro})');
rep('stage=s.stage;roleChoice=s.roleChoice','stage=s.stage;roleChoice=s.roleChoice;roundIntro=s.roundIntro');
rep('local function applyInput(player,event,value)\n',"local function applyInput(player,event,value)\n if phase~='fight' and event~='restart' then return end\n");
rep(" if phase~='fight' and event~='restart' then return end"," if phase~='fight' or event=='restart' or event=='role' or event=='stage' then return end");
rep("or kind=='overhead'", "or kind=='overhead' or kind=='teleport'");
rep("(kind=='special' or kind=='rising' or kind=='low')", "(kind=='special' or kind=='teleport' or kind=='e2' or kind=='e3' or kind=='rising' or kind=='low')");
rep("elseif event=='clickLight' then", "elseif event=='skill' then input.special=12;motionMove='special' elseif event=='ultimate' then input.special=12;motionMove='super' elseif event=='clickLight' then");
rep('local allowed={left=true,','local allowed={skill=true,ultimate=true,left=true,');
const poseBegin=source.indexOf(' local a=f[i];local art=actorNode(i,\'Art\');local pose=1'),poseEnd=source.indexOf('\n if spriteCache[i]~=key then',poseBegin);
assert.ok(poseEnd>poseBegin);
source=source.slice(0,poseBegin)+` local a=f[i];local art=actorNode(i,'Art');local ids=poseIds[a.role];local pose=ids.idle
 if a.down>0 then pose=ids.down
 elseif a.wake>0 then pose=ids.getup
 elseif a.launched then pose=ids.airHurt
 elseif a.stun>0 then pose=ids.hurt
 elseif a.attack then
  local atk=a.attack;local s=specs[a.role][atk.kind];local active=atk.t>=atk.startup
  if atk.kind=='low' then pose=active and ids.low or ids.crouch
  elseif atk.kind=='special' then pose=a.role==1 and ids.eThrow or ids.e1
  elseif atk.kind=='teleport' then pose=active and ids.teleport or ids.eThrow
  elseif atk.kind=='e2' then pose=ids.e2
  elseif atk.kind=='e3' then pose=active and ids.e3 or ids.e3Windup
  elseif atk.kind=='super' then pose=active and ids.qRelease or(ids.qCharge or ids.guard)
  else pose=active and(atk.kind=='rising' and ids.rising or ids.slash)or ids.windup end
  if atk.t>atk.startup+s.active+s.recovery*.7 then pose=ids.idle end
 elseif a.y>0 then pose=ids.jump
 elseif a.block then pose=a.crouch and ids.crouchGuard or ids.guard
 elseif a.crouch then pose=ids.crouch
 else local c=controls[i] and controls[i].input
  if c and(c.left or c.right)then pose=math.floor(a.walk/1.6)%2==0 and ids.walk1 or ids.walk2
  elseif ids.idle2 and math.floor(tick/40)%2==1 then pose=ids.idle2 end
 end
 local key=a.role*100+pose`+source.slice(poseEnd);
rep('local count=#data.rows;local previous=visualCounts[i] or 2275',`local count=#data.rows;local previous=visualCounts[i] or ${poolSize}`);
rep("art:SetLocalRotation(0,0,a.down>0 and -90*a.face or (a.launched and -35*a.face or lean*a.face))",'art:SetLocalRotation(0,0,0)');
rep('art:SetLocalScale(a.face,a.crouch and .60 or 1,1)','art:SetLocalScale(a.face,1,1)');
rep("actors[i]:SetAnchoredPosition(a.x,-155+a.y)","actors[i]:SetAnchoredPosition(a.x,-182+a.y);rootNode('Shadow'..i):SetAnchoredPosition(a.x,-184);rootNode('Shadow'..i):SetSizeDelta(math.max(24,68-a.y*.14),5)");
rep('art:SetAnchoredPosition(0,a.down>0 and 18 or 0)',"art:SetAnchoredPosition(0,not a.attack and a.down<=0 and a.y==0 and not a.crouch and a.stun<=0 and math.sin(tick/20)*1.1 or 0)");
const fxBegin=source.indexOf("  local fx=actorNode(i,'SpecialFx');"),fxEnd=source.indexOf('\n  hpBars[i]',fxBegin);
assert.ok(fxEnd>fxBegin);
source=source.slice(0,fxBegin)+`  local fx=actorNode(i,'SpecialFx');fx:SetVisible(false)
  local mark=actorNode(i,'Stiletto');mark:SetVisible(a.role==1 and(a.markLife or 0)>0)
  if (a.markLife or 0)>0 then mark:SetAnchoredPosition((a.markX or a.x)-a.x,92)end
  local bird=actorNode(i,'Phoenix');local atk=a.attack
  local birdOn=a.role==2 and atk and atk.kind=='super' and atk.t>=atk.startup and atk.t<atk.startup+specs[2].super.active
  bird:SetVisible(birdOn or false)
  if birdOn then
   local pose=math.floor((atk.t-atk.startup)/7)%2+1
   drawPhoenix(i,pose);bird:SetLocalScale(a.face,1,1);bird:SetAnchoredPosition(a.face*(90+(atk.t-atk.startup)*14),95)
  end
  for n=1,4 do
   local slash=actorNode(i,'BurstLine'..n)
   local on=a.role==1 and atk and atk.kind=='super' and atk.t>=atk.startup-5 and atk.t<atk.startup+specs[1].super.active
   slash:SetVisible(on or false)
  end
  local flame=actorNode(i,'FlameArc');local flaming=a.role==2 and atk and(atk.kind=='special' or atk.kind=='e2' or atk.kind=='e3')
  flame:SetVisible(flaming or false)
  if flaming then flame:SetLocalScale(a.face,1,1);flame:SetAnchoredPosition(a.face*95,atk.kind=='e3' and 70 or 105);flame:SetLocalRotation(0,0,atk.kind=='e2' and 30 or -25)end`+source.slice(fxEnd);
const renderFx=`
local fxNodes,fxPose={},{}
local function drawPhoenix(i,pose)
 if fxPose[i]==pose then return end
 local data=phoenixData[pose];local pool=actorNode(i,'Phoenix');fxNodes[i]=fxNodes[i] or {}
 for n=1,${fxPool} do
  local node=fxNodes[i][n];if not node then node=pool:FindChild('F'..n);fxNodes[i][n]=node end
  local r=data.rows[n];node:SetVisible(r~=nil)
  if r then node:SetAnchoredPosition((r[1]+r[3]/2-data.anchor[1])*data.scale,(data.anchor[2]-r[2]-r[4]/2)*data.scale);node:SetSizeDelta(r[3]*data.scale,r[4]*data.scale);node.imageColor=r[5]end
 end
 fxPose[i]=pose
end
`;
rep('local function drawStage()',renderFx+'\nlocal function drawStage()');
rep(' drawnStage=stage',` drawnStage=stage
 local data=stageArtData[stage];local pool=rootNode('BackdropArt')
 for n=1,${stagePool} do
  local node=stageArtNodes[n];if not node then node=pool:FindChild('B'..n);stageArtNodes[n]=node end
  local r=data.rows[n];node:SetVisible(r~=nil)
  if r then node:SetAnchoredPosition((r[1]+r[3]/2-data.anchor[1])*data.scale,(data.anchor[2]-r[2]-r[4]/2)*data.scale);node:SetSizeDelta(r[3]*data.scale,r[4]*data.scale);node.imageColor=r[5]end
 end`);
rep('local drawnStage=nil','local stageArtData={'+stages.map(luaFrame).join(',')+'}\nlocal stageArtNodes={}\nlocal drawnStage=nil');
// Insert local menus after rb declaration and request helpers, before callbacks.
const menu=readFileSync('work/vnext-menu.lua','utf8').replace('local roundIntro=90\n','');
source=source.slice(0,source.indexOf('local spriteCache='))+'local portraitData={'+['keqing','diluc'].map(r=>luaFrame(portraits[r])).join(',')+'}\nlocal portraitPool='+portraitPool+'\n'+source.slice(source.indexOf('local spriteCache='));
rep('function OnStart()\n script:RegisterServerSignalHandler',menu+"\nlocal oldInit=OnInit\nfunction OnInit()oldInit();menuDraw()end\nfunction OnStart()\n menuStart()\n rootNode('Skill'):AddCursorEventListener(Enum.CursorEventType.CursorClick,function()sendInput('skill')end)\n rootNode('Ultimate'):AddCursorEventListener(Enum.CursorEventType.CursorClick,function()sendInput('ultimate')end)\n script:RegisterServerSignalHandler");
rep("sig:AddString(payload);sig:SendSignal();debugNet.tx",'sig:AddString(payload);sig:AddInt(menuEpoch);sig:SendSignal();debugNet.tx');
// flushFrames precedes menu definitions: epoch must be declared before it.
rep("local menuEpoch=1\n",'');rep('local rb=nil','local menuEpoch=1\nlocal rb=nil');
rep('if not rb or tonumber(params[1])~=3-seat then return end','if not rb or tonumber(params[1])~=3-seat or tonumber(params[5])~=menuEpoch then return end');
rep('if onlineReady or (seat~=1 and seat~=2)then return end','if onlineReady or (seat~=1 and seat~=2)or not menuReady[1] or not menuReady[2] then return end');
rep('onlineReady=true;restart();acc=0','onlineReady=true;menuMode=\'battle\';restart();acc=0');
rep('if seat==2 and not joined then joined=true;joinRequest()end','sendSelection()');
rep("for _,e in ipairs({{'RoleKeqing',1},{'RoleDiluc',2}})do root:FindChild(e[1]):AddCursorEventListener(Enum.CursorEventType.CursorClick,function()sendInput('role',e[2])end)end", "for _,e in ipairs({{'RoleKeqing',1},{'RoleDiluc',2}})do root:FindChild(e[1]):AddCursorEventListener(Enum.CursorEventType.CursorClick,function()chooseRole(e[2])end)end");
rep("function()sendInput('stage',n)end)","function()chooseStage(n)end)");
rep(' visualUpdates=visualUpdates+1',' menuTime=menuTime+dt\n visualUpdates=visualUpdates+1');
rep('if not onlineReady then if seat==2 then joinRequest()else helloRequest()end end',"if not onlineReady then\n   if seat==0 then helloRequest()else sendSelection();if seat==2 and menuReady[1] and menuReady[2] then joinRequest()end end\n  end");
rep(' if not onlineReady or not rb then return end'," if not onlineReady or not rb then menuDraw();return end");
rep(" elseif rb.stalled then status.text=", " elseif rb.stalled then status.text=");
const disable=source.indexOf('\nfunction OnDisable()',source.indexOf('local resendTime=0'));
source=source.slice(0,disable).replace(/\nend\s*$/,'\n menuDraw()\nend\n')+source.slice(disable);
// All UI strings retain the working decimal-escaped UTF-8 device format.
source=source.replace(/[^\x00-\x7f]/gu,c=>[...Buffer.from(c)].map(n=>'\\'+n.toString().padStart(3,'0')).join(''));
const save=JSON.parse(readFileSync('outputs/demo-online-light-rollback-diagnostic/fighter.save.json'));
const host=save.assets.server.root.children[0];
const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean);
const pixel=structuredClone(find(host,'Hp1')),label=structuredClone(find(host,'Status')),button=structuredClone(find(host,'Light')),group=structuredClone(find(host,'Art'));
let seq=0,guid=1270000000;
function add(t,name,x,y,w,h,p=host,front=true){const n=structuredClone(t);n.id='vnext_'+(++seq);n.guid=guid++;n.name=name;n.children=[];n.active=true;n.visible=true;n.raycastTarget=false;delete n.scriptMappingIds;delete n.giaRelatedGuids;
 for(const a of Object.values(n.transformByPlatform)){a.offset={x,y};a.size={x:w,y:h};a.scale={x:1,y:1,z:1};a.rotation={x:0,y:0,z:0};a.anchorMin=a.anchorMax={x:.5,y:.5};a.pivot={x:.5,y:.5};}front?p.children.unshift(n):p.children.push(n);return n;}
const box=(name,x,y,w,h,c,p=host,front=true)=>{const n=add(pixel,name,x,y,w,h,p,front);n.imageColor=Number('0xff'+c)>>>0;return n;};
const tx=(name,text,x,y,w=400,size=18,p=host)=>{const n=add(label,name,x,y,w,40,p);n.text=text;n.fontSize=size;return n;};
const btn=(name,text,x,y,w=160,h=48,p=host)=>{const n=add(button,name,x,y,w,h,p);n.raycastTarget=true;box(name+'Surface',0,0,w,h,['StartDuel','ReadyConfirm'].includes(name)?'665985':'28374c',n,false);tx(name+'Text',text,0,0,w,18,n);return n;};
function pixels(p,name,data,scale=data.scale){const g=add(group,name,0,0,1,1,p);for(const r of data.rows){const n=box(name+'Px'+(++seq),(r[0]+r[2]/2-data.anchor[0])*scale,(data.anchor[1]-r[1]-r[3]/2)*scale,r[2]*scale,r[3]*scale,'ffffff',g);n.imageColor=((r[7]<<24)|(r[4]<<16)|(r[5]<<8)|r[6])>>>0;}return g;}
for(let i=0;i<2;i++){
 const actor=find(host,i?'Diluc':'Keqing'),art=find(actor,'Art'),pool=find(art,'Sprite');
 for(let n=pool.children.length;n<poolSize;n++){const p=box('P'+(n+1),0,0,1,1,'ffffff',pool);p.visible=false;}
 const bird=add(group,'Phoenix',0,95,1,1,actor);bird.visible=false;
 for(let n=1;n<=fxPool;n++){const p=box('F'+n,0,0,1,1,'ffffff',bird);p.visible=false;}
 const mark=box('Stiletto',0,92,18,5,'bc9dff',actor);for(const a of Object.values(mark.transformByPlatform))a.rotation.z=35;mark.visible=false;
 for(let n=1;n<=4;n++){const line=box('BurstLine'+n,80,60+n*23,260,3,n%2?'e6caff':'ad88ff',actor);for(const a of Object.values(line.transformByPlatform))a.rotation.z=(n%2?1:-1)*(10+n*8);line.visible=false;}
 const flame=add(group,'FlameArc',95,105,1,1,actor);flame.visible=false;
 for(let n=0;n<8;n++)box('Flame'+n,-80+n*24,Math.sin(n/7*Math.PI)*35,28,8,n%2?'ffc857':'ee6234',flame);
 const portrait=add(group,'Portrait'+(i+1),i?-598:598,285,1,1);box('FaceFrame'+i,0,0,60,67,i?'b75939':'735394',portrait);
 for(let n=1;n<=portraitPool;n++){const p=box('FacePx'+n,0,0,1,1,'ffffff',portrait);p.visible=false;}
 for(let n=1;n<=2;n++)box('Win'+(i+1)+n,(i?1:-1)*(124+n*22),275,12,12,'eacb7e');
 const shadow=box('Shadow'+(i+1),0,-184,68,5,'222c28',host,false);shadow.imageColor=0x660b1717;
}
for(let n=1;n<=3;n++){
 const p=find(host,'Stage'+n);for(const name of ['Ground','GroundLine'])find(p,name).visible=false;
 for(const node of p.children)node.visible=false;
 for(const node of p.children)if(node.name.startsWith('Paving'))node.visible=false;
 p.children=[]; // New candidate hierarchy only; preserve the old version and source files.
 box('GroundTop',0,-197,1280,88,n===1?'86906b':'93958b',p);
 box('GroundBackEdge',0,-153,1280,5,'b9bda3',p);
 box('GroundFront',0,-250,1280,24,n===1?'4e5942':'565c5c',p);
 box('GroundLip',0,-236,1280,5,'b9b6a0',p);
 for(let r=0;r<3;r++){
  box('TileRow'+r,0,-174-r*25,1280,2,'717760',p);
  for(let k=0;k<12;k++){const x=-600+k*110+(r%2)*55;box('TileCut'+r+'_'+k,x,-163-r*25,2,22,'717760',p);}
 }
 if(n===1){for(let k=0;k<20;k++)box('Grass'+k,-605+k*63,-144,20,4,k%3?'708757':'a8b574',p);}
 if(n===2){for(const x of [-550,550]){box('BridgePost'+x,x,-120,30,66,'b8b5a4',p);box('BridgePostTop'+x,x,-84,45,9,'d7cfb6',p);}box('BridgeRail',0,-110,1100,9,'d2c8b4',p);}
 if(n===3){for(let k=0;k<16;k++)box('Rubble'+k,-590+k*77,-145,20+k%3*8,12+k%2*8,'767d74',p);}
}
const backdrop=add(group,'BackdropArt',0,-153,1,1,host,false);
for(let n=1;n<=stagePool;n++){const p=box('B'+n,0,0,1,1,'ffffff',backdrop);p.visible=false;}
const home=add(group,'HomeScreen',0,0,1,1);box('HomeBackdrop',0,0,1280,720,'121a2a',home,false);
for(let k=0;k<8;k++){const n=box('HomeStripe'+k,-480+k*155,35,90,760,k%2?'1d293e':'1b2537',home);for(const t of Object.values(n.transformByPlatform))t.rotation.z=-18;}
tx('GameTitle','原神格斗',0,150,900,58,home);tx('GameSubtitle','雷光与黎明',0,85,650,26,home);tx('GameMode','双人对战 · 单角色 · 三局两胜',0,12,900,20,home);
btn('StartDuel','开始双人对战',0,-95,280,62,home);tx('StartHelp','先选人，再由双方确认开战',0,-165,800,17,home);
const select=add(group,'SelectScreen',0,0,1,1);host.children.splice(host.children.indexOf(select),1);host.children.splice(host.children.findIndex(n=>n.name==='Keqing')+2,0,select);
box('SelectBackdrop',0,0,1280,720,'182335',select,false);box('PreviewPanel1',-310,86,440,400,'233047',select);box('PreviewPanel2',310,86,440,400,'302c36',select);
tx('SelectTitle','选择角色',0,302,800,30,select);tx('SelectName1','P1 刻晴',-310,225,350,24,select);tx('SelectName2','P2 迪卢克',310,225,350,24,select);
tx('SelectReady1','',-310,-115,420,18,select);tx('SelectReady2','',310,-115,420,18,select);tx('SelectionHint','',0,165,550,18,select);
for(const [name,role,x]of[['ChooseKeqing','keqing',-105],['ChooseDiluc','diluc',105]]){const b=btn(name,role==='keqing'?'刻晴':'迪卢克',x,-215,165,110,select);b.children[0].transformByPlatform=structuredClone(b.children[0].transformByPlatform);for(const t of Object.values(b.children[0].transformByPlatform))t.offset.y=-37;const face=pixels(b,name+'Face',portraits[role]);for(const t of Object.values(face.transformByPlatform))t.offset.y=16;}
btn('ReadyConfirm','确认准备',0,-310,210,46,select);btn('BackHome','返回',-465,-310,110,46,select);
for(let n=1;n<=3;n++){const b=find(host,'SelectStage'+n);for(const t of Object.values(b.transformByPlatform))t.offset={x:(n-2)*132,y:-145};}
const result=add(group,'ResultScreen',0,0,1,1);box('ResultBackdrop',0,0,650,380,'152237',result,false);tx('ResultTitle','',0,100,550,42,result);tx('ResultScore','',0,35,550,26,result);
btn('Rematch','再战',-180,-85,150,52,result);btn('Reselect','重新选人',0,-85,150,52,result);btn('ResultHome','返回开始',180,-85,150,52,result);
tx('RoundBanner','ROUND ONE',0,55,900,44);
btn('DebugToggle','诊断',0,338,70,30);
btn('Skill','特殊技 E',185,-317,112,45);btn('Ultimate','必杀 Q',315,-317,112,45);
find(host,'MotionHelp').visible=false;find(host,'Help').text='A/D 移动 · S 蹲伏 · 空格 跳跃 · J 轻攻 · K 重攻 · L 防御 · 特殊技/必杀也可搓招';
for(const name of ['Light','Heavy','Jump','Block',...Array.from({length:9},(_,i)=>'Stick'+(i+1)),...Array.from({length:3},(_,i)=>'SelectStage'+(i+1))]){
 const b=find(host,name),t=Object.values(b.transformByPlatform)[0];box(name+'Surface',0,0,t.size.x,t.size.y,name==='Light'?'50446b':name==='Heavy'?'754739':'28374c',b,false);
}
for(const t of Object.values(find(host,'Help').transformByPlatform))t.offset.y=-352;
save.assets.scripts[0].source=source;save.assets.scripts[0].filename='fighter_online_rollback_debug.lua';
save.meta.name='原神格斗 · 双人下一版候选 · 动作与菜单';
save.assets.server.root.name='FighterDuelNext';
let compactGuid=1073741850,controlsCount=0;const controlIds=new Set();
const compact=n=>{assert.ok(!controlIds.has(n.id),'duplicate '+n.id);controlIds.add(n.id);n.guid=compactGuid++;controlsCount++;delete n.giaRelatedGuids;delete n.giaInfoIndex;delete n.scriptMappingIds;for(const c of n.children||[])compact(c);};
compact(save.assets.server.root);controlIds.clear();if(save.assets.client?.root)compact(save.assets.client.root);
const script=save.assets.scripts[0];script.guid=compactGuid++;script.id=String(script.guid);script.controlId=host.id;script.controlAsset='';script.path='lua/fighter_duel_vnext.lua';script.filename='fighter_duel_vnext.lua';
save.assets.server.meta.name='FighterDuelNext';delete save.assets.server.meta.giaFilePath;save.assets.server.meta.giaFileName='原神格斗_双人下一版候选.gia';save.assets.server.meta.giaFileId=save.assets.server.root.guid;
save.serverLogic={version:1,rules:[
 {id:'seats',signalName:'FighterHello',actions:[1,2].map(i=>({kind:'sendClientScriptSignal',target:'Player'+i,signalName:'FighterSeat',params:[i]}))},
 {id:'selection',signalName:'FighterSelect',actions:[{kind:'sendClientScriptSignal',target:'AllPlayers',signalName:'FighterSelectOut',params:Array.from({length:6},(_,i)=>({fromSignalParam:i}))}]},
 {id:'join',signalName:'FighterJoin',actions:[{kind:'sendClientScriptSignal',target:'AllPlayers',signalName:'FighterJoined',params:[]}]},
 {id:'frames',signalName:'FighterFrames',actions:[{kind:'sendClientScriptSignal',target:'AllPlayers',signalName:'FighterFramesOut',params:Array.from({length:5},(_,i)=>({fromSignalParam:i}))}]}
]};
writeFileSync(out+'/fighter_duel_vnext.lua',source);writeFileSync(out+'/fighter.save.json',JSON.stringify(save));writeFileSync(out+'/server-logic.json',JSON.stringify(save.serverLogic,null,2));
const ex=createStudio(save).exportData('gia-combined'),buffer=Buffer.from(ex.data,ex.encoding),valid=validateServerGiaCompatibility(buffer);assert.ok(valid.valid,JSON.stringify(valid));
const imported=importGia(buffer,'原神格斗_双人下一版候选.gia');assert.ok(imported.scripts.some(s=>s.source.includes('menuReady')&&s.path==='lua/fighter_duel_vnext.lua'),'round-trip script mapping');
writeFileSync(out+'/原神格斗_双人下一版候选.gia',buffer);
const countKind=(n,kind)=>(n.kind===kind?1:0)+(n.children||[]).reduce((a,c)=>a+countKind(c,kind),0);
writeFileSync(out+'/build.json',JSON.stringify({candidate:true,deviceVerified:false,giaCompatible:valid.valid,giaRoundTrip:true,giaBytes:buffer.length,controlCount:controlsCount,guidRange:[1073741850,compactGuid-1],scriptPath:script.path,poolPerFighter:poolSize,sharedActorPools:poolSize*2,fxPoolPerFighter:fxPool,stagePool,residentImages:countKind(host,'image'),portraitRows:portraits.keqing.rows.length+portraits.diluc.rows.length,frameCounts:sets.map(s=>s.frames.length),serverLogicIncludedInGia:false},null,2));
console.log(JSON.stringify({out,poolSize,fxPool,bytes:buffer.length,frames:sets.map(s=>s.frames.length)}));
