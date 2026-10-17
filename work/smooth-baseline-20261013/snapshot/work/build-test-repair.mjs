import{readFileSync as read,writeFileSync as write,mkdirSync,copyFileSync}from'node:fs';
import assert from'node:assert/strict';
const old=process.env.REPAIR_INPUT||'outputs/group1-full-test',out=process.env.REPAIR_OUT||'outputs/test-repair-v1';mkdirSync(out,{recursive:true});
const save=JSON.parse(read(old+'/base.save.json'));let source=save.assets.scripts[0].source;
const rep=(a,b)=>{assert(source.includes(a),'missing '+a.slice(0,70));source=source.replace(a,b);};
rep('local roundWinner=0',read('work/repair-collision.lua','utf8')+'\nlocal roundWinner=0');
rep('local function restart()round=1;', 'local function restart()Collision.results={};round=1;');
rep('roundWinner=winner\n', 'roundWinner=winner;Collision.results[round]=winner\n');
rep(" or math.abs(b.y-a.y)>(s.heightRange or 75)", '');
rep('if distance<0 or distance>range+20 then return end', 'if not Collision.overlap(Collision.attack(a,s,range),Collision.hurt(b))then return end');
rep('if a.down<=0 and b.down<=0 and math.abs(gap)<50 and math.abs(a.y-b.y)<75 then local direction=gap>=0 and 1 or -1;local push=(50-math.abs(gap))/2;a.x=clamp(a.x-direction*push,-535,535);b.x=clamp(b.x+direction*push,-535,535)end','Collision.push(a,b)');
rep('roundWinner=roundWinner})','roundWinner=roundWinner,collisionResults=Collision.results})');
rep('roundWinner=s.roundWinner or 0','roundWinner=s.roundWinner or 0;Collision.results=s.collisionResults or{}');
rep('local resourceGate={busy=true,mode=\'menu\',caps={0,0},request=nil}', "local resourceGate={busy=true,mode='menu',caps={0,0},request=nil,collision=Collision}");
rep('plannedRound=1;teamScores={0,0};teamChoice=', 'Collision.results={};plannedRound=1;teamScores={0,0};teamChoice=');
rep('resourceGate.menuRoles=function()return previewChoice,rosterPage end', "resourceGate.menuRoles=function()return previewChoice,rosterPage end\n resourceGate.teamRoles=function()return teamChoice end\n resourceGate.prefetchRoles=function()return{menuMode=='select'and menuReady[1]and teamChoice[1][1]or 0,menuMode=='select'and menuReady[2]and teamChoice[2][1]or 0}end");
function find(n,name){if(n.name===name)return n;for(const c of n.children||[]){const r=find(c,name);if(r)return r;}}
const host=find(save.assets.server.root,'FighterDemo'),group=find(host,'Art'),image=find(host,'Hp1'),text=find(host,'GameTitle');let id=0;
function add(proto,name,parent,x,y,w,h){const n=structuredClone(proto);n.children=[];n.name=name;n.id='repair_'+(++id);n.guid=1076100000+id;n.raycastTarget=false;delete n.scriptMappingIds;for(const t of Object.values(n.transformByPlatform)){t.offset={x,y};t.size={x:w,y:h};t.scale={x:1,y:1,z:1};t.anchorMin=t.anchorMax=t.pivot={x:.5,y:.5};}parent.children.unshift(n);return n;}
const hud=add(group,'BattleTeamHUD',host,0,0,1,1);
for(let p=1;p<=2;p++)for(let n=1;n<=3;n++){
 const x=(p===1?-1:1)*(480-(n-1)*100),y=220,name='BattleTeam'+p+n;
 const plate=add(image,name+'Plate',hud,x,y,94,72);plate.imageColor=p===1?0xff295a82:0xff8b3944;
 const face=add(group,name+'Face',hud,x,y+4,1,1);save._pixelJobs.push({path:['BattleTeamHUD',face.name],prefix:'TeamPx',count:400});
 const label=add(text,name+'Text',hud,x,y-26,90,18);label.fontSize=11;label.minimumFontSize=11;label.text='';
}
for(let p=1;p<=2;p++)for(const kind of['Push','Hurt','Attack']){const n=add(image,'Collision'+kind+p,host,0,0,1,1);n.visible=false;n.imageColor=kind==='Push'?0x553377ff:kind==='Hurt'?0x5500ff66:0x55ff3333;}
rep('local function menuDraw()',`function Collision.drawHUD(fighting)
 local host=rootNode('BattleTeamHUD');host:SetVisible(fighting)
 Collision.hudNodes=Collision.hudNodes or{};Collision.hudKeys=Collision.hudKeys or{}
 for p=1,2 do for n=1,3 do
  local name='BattleTeam'..p..n;local role=teamChoice[p][n];local winner=Collision.results[n]
  local state=winner~=nil and(winner==0 and'draw'or winner==p and'win'or'loss')or(n==round and'active'or'wait')
  local plate=host:FindChild(name..'Plate');plate.imageColor=state=='loss'and 0xff444444 or state=='active'and 0xffb6a466 or(p==1 and 0xff295a82 or 0xff8b3944)
  host:FindChild(name..'Text').text=role>0 and(roleNames[role]..(state=='win'and' ✓'or state=='draw'and' 平'or''))or''
  local key=role..':'..state;if fighting and role>0 and Collision.hudKeys[name]~=key then
   local data=thumbData[role];if data.rows then
    local frame=data;if state=='loss'then local palette={};for k,c in ipairs(data.palette)do local r=math.floor(c/65536)%256;local g=math.floor(c/256)%256;local b=c%256;local gray=math.floor(r*.299+g*.587+b*.114);palette[k]=math.floor(c/16777216)*16777216+gray*65793 end;frame={rows=true,count=data.count,raw=data.raw,palette=palette,anchor=data.anchor}end
    Collision.hudNodes[name]=Collision.hudNodes[name]or{};paintFrame(host:FindChild(name..'Face'),'TeamPx',frame,1.3,Collision.hudNodes[name]);Collision.hudKeys[name]=key
   end
  end
 end end
end
function Collision.drawBoxes()
 for p=1,2 do local a=f[p];local profile=Collision.profiles[a.role]
  local boxes={Push={a.x-profile.push,a.y,a.x+profile.push,a.y+profile.height},Hurt=Collision.hurt(a)}
  if a.attack then local s=specs[a.role][a.attack.kind];if a.attack.t>=a.attack.startup and a.attack.t<a.attack.startup+s.active then boxes.Attack=Collision.attack(a,s,s.range)end end
  for _,kind in ipairs({'Push','Hurt','Attack'})do local node=rootNode('Collision'..kind..p);local b=boxes[kind];node:SetVisible(menuMode=='battle'and debugPanel and b~=nil);if b then node:SetAnchoredPosition((b[1]+b[3])/2,-182+(b[2]+b[4])/2);node:SetSizeDelta(b[3]-b[1],b[4]-b[2])end end
 end
end
local function menuDraw()`);
rep("rootNode('HomeScreen'):SetVisible(menuMode=='home');", "Collision.drawHUD(fighting);Collision.drawBoxes();rootNode('HomeScreen'):SetVisible(menuMode=='home');");
rep('resourceGate.completed=function(mode)', 'resourceGate.completed=function(mode)Collision.hudNodes={};Collision.hudKeys={};');
rep('draw()\n if lastDrawPhase', 'draw();Collision.drawBoxes()\n if lastDrawPhase');
rep('if valid then', 'if valid and selecting then');
rep("paintFrame(rootNode('GridFace'..n),'IconPx',thumbData[role],2.3,gridNodes[n])", "if gridRoles[n]~=role then paintFrame(rootNode('GridFace'..n),'IconPx',thumbData[role],2.3,gridNodes[n]);gridRoles[n]=role end");
rep('paintFrame(bust,\'HomePx\',resourceGate.homePortraitData[i],resourceGate.homePortraitData[i].scale*hs,resourceGate.homePortraitNodes[i])', "local key=cw..':'..ch;resourceGate.homePaintKeys=resourceGate.homePaintKeys or{};if resourceGate.homePaintKeys[i]~=key then paintFrame(bust,'HomePx',resourceGate.homePortraitData[i],resourceGate.homePortraitData[i].scale*hs,resourceGate.homePortraitNodes[i]);resourceGate.homePaintKeys[i]=key end ");
rep('resourceGate.homePortraitNodes={{},{}};menuDirty=true', 'resourceGate.homePortraitNodes={{},{}};resourceGate.homePaintKeys={};menuDirty=true');
save.assets.scripts[0].source=source;write(out+'/base.save.json',JSON.stringify(save));
for(const f of['roster.json','motion-integration.json'])copyFileSync(old+'/'+f,out+'/'+f);
write(out+'/collision-config.json',JSON.stringify({status:'initial editable collision candidate; needs manual calibration',normal:{pushHalfWidth:26,hurtHalfWidth:26,height:166,crouchHeight:94},smallRoles:[5,39],largeRole:11,projectileArtPending:true},null,2));
console.log('REPAIR_BASE_READY');
