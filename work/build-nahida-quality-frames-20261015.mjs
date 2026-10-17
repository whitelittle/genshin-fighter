import fs from 'node:fs';import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {createNode} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/ui/authoring.js';
import {exportGia,importGia,validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const OUT='outputs/nahida-quality-frames-20261015';
const animation=JSON.parse(fs.readFileSync(OUT+'/animation.json'));const baseline=JSON.parse(fs.readFileSync('outputs/full-reinstall/simulator.save.json'));
let guid=1076500000;
const ids={rectangle:100001,ellipse:100002,triangle:100003,fourstar:100004};
const make=(kind,name,extra={})=>createNode(kind,{id:'na'+guid,guid:guid++,name,syncAllDevices:false,...extra});
function place(n,x,y,w,h,r=0,s=1){for(const t of Object.values(n.transformByPlatform)){t.anchorMin=t.anchorMax=t.pivot={x:.5,y:.5};t.offset={x,y};t.size={x:w,y:h};t.rotation={x:0,y:0,z:r};t.scale={x:s,y:s,z:1};}return n;}
const root=make('server-container','草神两组原生图元动作试验'),stage=place(make('container','AnimationStage'),0,0,1600,900),actor=place(make('container','Actor'),0,-15,animation.w,animation.h,0,1.35);root.children=[stage];stage.children=[actor];
const first=animation.actions[0].frames[0].elements;
for(let i=0;i<first.length;i++){const e=first[i];actor.children.push(place(make('image','S'+String(i).padStart(4,'0'),{imageId:ids[e.type],imageColor:(0xff000000|parseInt(e.color.slice(1),16))>>>0}),e.x-animation.w/2,animation.h/2-e.y,e.width,e.height,e.rotation));}
const label=(name,text,x,y,w=300)=>{const n=make('textbox',name,{text,fontSize:22,minimumFontSize:22,fontColor:0xff3a423b,bgColor:0,enableOutline:false,horizontalAlignment:'Middle',verticalAlignment:'Middle'});stage.children.push(place(n,x,y,w,40));return n;};
label('Status','idle 1/4',0,370,900);label('Hint','994 matched images / frame animation / art not approved',0,-405,1450);
actor.children.reverse();stage.children.reverse();
const banks=animation.actions.map(a=>a.frames.map(f=>'{'+[...f.elements].sort((a,b)=>a.poolId-b.poolId).map(e=>'{'+[e.x-animation.w/2,animation.h/2-e.y,e.width,e.height,e.rotation,...[1,3,5].map(i=>parseInt(e.color.slice(i,i+2),16)),f.elements.indexOf(e)].map(v=>Number(v.toFixed(4))).join(',')+'}').join(',')+'}'));
const lua=`local frames={idle={${banks[0].join(',')}},move={${banks[1].join(',')}}}
local controls,actor,status,last={},nil,nil,nil
local action,index,clock,paused='idle',1,0,true
local function publish()
 local rows=frames[action][index]
 if last~=rows then
  local order={}
  for i,p in ipairs(rows) do order[p[9]+1]=controls[i] end
  for _,c in ipairs(order) do c:SetAsLastSibling() end
  for i,p in ipairs(rows) do
   local c=controls[i]
   c:SetAnchoredPosition(p[1],p[2]);c:SetSizeDelta(p[3],p[4])
   c:SetLocalRotation(0,0,p[5]);c.imageColor=Color(p[6],p[7],p[8],255)
  end
  last=rows
 end
 status.text=action..' '..index..'/4'..(paused and ' paused' or '')..' frames'
end
local function command(op,value)
 if op=='action' then action=value=='move' and 'move' or 'idle';index=1;clock=0
 elseif op=='pause' then paused=value==1;clock=0
 elseif op=='step' then paused=true;index=index%4+1;clock=0
 elseif op=='frame' then paused=true;index=math.max(1,math.min(4,tonumber(value) or 1));clock=0
 elseif op=='mirror' then actor:SetLocalScale(value==-1 and -1.35 or 1.35,1.35,1)
 elseif op=='position' then actor:SetAnchoredPosition(math.max(-400,math.min(400,tonumber(value) or 0)),-15)
 end
 publish()
end
function OnStart()
 actor=script.object:FindChild('Actor');status=script.object:FindChild('Status')
 for i=1,${first.length} do controls[i]=actor:FindChild('S'..string.format('%04d',i-1)) end
 script:RegisterServerSignalHandler('AnimationControl',function(_,p)command(p[1],p[2])end)
 publish();script:EnableUpdate(true)
end
function OnUpdate(dt)
 if paused then return end
 clock=clock+(dt or 1/60)
 if clock>=.18 then
  local steps=math.floor(clock/.18);clock=clock%.18;index=(index-1+steps)%4+1;publish()
 end
end
`;
const template=structuredClone(baseline.assets.scripts[0]);Object.assign(template,{guid:1076599999,id:'nahida-animation',filename:'nahida-two-actions.lua',path:'lua/nahida-two-actions.lua',controlId:stage.id,source:lua});stage.scriptMappingIds=[template.guid];
const save={format:baseline.format,version:baseline.version,meta:{name:root.name},activeAssetType:baseline.activeAssetType,serverLogic:{version:1,rules:[]},assets:{server:{...baseline.assets.server,root,meta:{...baseline.assets.server.meta,name:root.name,giaFileName:'草神_994图元_高清逐帧.gia',giaFileId:root.guid,sourceFile:''}},client:structuredClone(baseline.assets.client),scripts:[template]}};save.assets.client.root.children=[];
const result=exportGia(save.assets.server,{scripts:save.assets.scripts});assert(validateServerGiaCompatibility(result.buffer).valid);fs.writeFileSync(OUT+'/草神_994图元_高清逐帧.gia',result.buffer);fs.writeFileSync(OUT+'/nahida-two-actions.lua',lua);
const actual=importGia(result.buffer,'草神_994图元_高清逐帧.gia');save.assets.server=actual.project;save.assets.scripts=actual.scripts;
for(const s of save.assets.scripts){const scan=n=>{if((n.scriptMappingIds||[]).includes(s.guid))s.controlId=n.id;for(const c of n.children||[])scan(c);};scan(actual.project.root);}
fs.writeFileSync(OUT+'/reimported.simulator.save.json',JSON.stringify(save));
const studio=createStudio(save);studio.playStart({canvasId:'pc-16-9'});studio.playStep(1/60,{observe:false});
const results=[];for(const action of animation.actions){studio.playServerSend('AnimationControl',['action',action.key]);for(let i=1;i<=4;i++){studio.playServerSend('AnimationControl',['frame',i]);studio.playStep(1/60,{observe:false});const state=studio.playGet({view:true,paint:true});assert.equal(state.logs.filter(l=>['error','lua-error'].includes(l.level)).length,0,JSON.stringify(state.logs));const images=state.scene.nodes.filter(n=>/^S\d{4}$/.test(n.name));assert.equal(images.length,994);const expected=[...action.frames[i-1].elements].sort((a,b)=>a.poolId-b.poolId);for(const n of images){const index=Number(n.name.slice(1));assert.equal(n.imageId,ids[expected[index].type]);assert(Math.abs((n.sourceWidth??n.width)-expected[index].width)<.01,JSON.stringify({name:n.name,width:n.width,sourceWidth:n.sourceWidth,expected:expected[index].width,keys:Object.keys(n)}));assert(Math.abs((n.sourceHeight??n.height)-expected[index].height)<.01);}results.push({action:action.key,frame:i,images:images.length,status:state.scene.nodes.find(n=>n.name==='Status').text});}}
studio.playServerSend('AnimationControl',['action','idle']);studio.playServerSend('AnimationControl',['pause',0]);for(let i=0;i<13;i++)studio.playStep(1/60,{observe:false});assert(studio.playGet({view:true}).scene.nodes.find(n=>n.name==='Status').text.includes('2/4'));studio.playStop();
fs.writeFileSync(OUT+'/verification.json',JSON.stringify({giaStructuralValidation:true,giaBytes:result.buffer.length,imagePoolSize:994,backgroundImageControls:0,actualGiaReimported:true,frames:results,nativePlaybackAdvanced:true,deviceVerified:false,artApproved:false},null,2));console.log(JSON.stringify({giaBytes:result.buffer.length,framesChecked:results.length,imagePoolSize:994}));
