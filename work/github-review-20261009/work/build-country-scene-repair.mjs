import{readFileSync as read,writeFileSync as write}from'node:fs';import assert from'node:assert/strict';import{packFrame,luaFrame}from'./v2-pack.mjs';
const out=process.env.REPAIR_OUT||'outputs/test-repair-v1',save=JSON.parse(read(out+'/base.save.json'));let source=save.assets.scripts[0].source;
const rep=(a,b)=>{assert(source.includes(a),'stage missing '+a.slice(0,60));source=source.replace(a,()=>b);};
const keys=['mondstadt','liyue','inazuma','sumeru','fontaine','natlan','snezhnaya'];
const names=['蒙德 · 风起地','璃月 · 望舒客栈','稻妻 · 清籁岛','须弥 · 赤王陵','枫丹 · 水都远景','纳塔 · 高山台地','至冬 · 雪境列车'];
// User-approved nearest-neighbor pixel-master pipeline. Preserve all earlier masters.
const stageSource=process.env.STAGE_PIXEL_OUT||'outputs/stage-pixel-nearest-v2',stageBudget=Number(process.env.STAGE_BUDGET||5000);
const frames=keys.map(k=>JSON.parse(read(stageSource+'/'+k+'-frame.json'))),packed=frames.map(packFrame);
rep('local Collision={results={},profiles={},moves={}}',`local Collision={results={},profiles={},moves={},stageData={${packed.map((p,i)=>luaFrame(p).slice(0,-1)+`,w=${frames[i].w},h=${frames[i].h}}`).join(',')}},stageNames={${names.map(n=>JSON.stringify(n)).join(',')}}}
function Collision.stageId(seed,number)
 local value=math.max(1,math.min(210,math.floor(seed or 1)))-1;local pool={1,2,3,4,5,6,7};local order={}
 order[1]=table.remove(pool,math.floor(value/30)+1);value=value%30
 order[2]=table.remove(pool,math.floor(value/5)+1);order[3]=pool[value%5+1]
 return order[math.max(1,math.min(3,number))]
end`);
rep("map>3 or not epoch", "map>210 or map~=math.floor(map)or not epoch");
rep('stage=math.random(1,3)', 'stage=math.random(1,210)');
rep("stage=clamp(value,1,3)", "stage=clamp(value,1,210)");
rep('resourceGate.teamRoles=function()return teamChoice end',`resourceGate.teamRoles=function()return teamChoice end
 resourceGate.stageFrame=function()return Collision.stageData[Collision.stageId(stage,plannedRound)]end`);
rep("rootNode('Stage'..n):SetVisible(fighting and stage==n)","rootNode('Stage'..n):SetVisible(false)");
rep("rootNode('StageTitle').text=({'风起地 · 七天神像与大树','蒙德 · 城门与大桥','风龙废墟 · 中央高塔'})[stage]", "rootNode('StageTitle').text=Collision.stageNames[Collision.stageId(stage,round)]");
rep('local function menuDraw()',`function Collision.drawStage(fighting)
 local parent=rootNode('CountryStage');parent:SetVisible(fighting)
 if not fighting then return end
 local id=Collision.stageId(stage,round);local cw,ch=game.GetUICanvasSize();local frame=Collision.stageData[id];local scale=math.max(cw/frame.w,ch/frame.h)
 local key=id..':'..cw..':'..ch
 if Collision.stagePaintKey~=key then Collision.stageNodes=Collision.stageNodes or{};paintFrame(parent,'StagePx',Collision.stageData[id],scale,Collision.stageNodes);Collision.stagePaintKey=key end
end
local function menuDraw()`);
rep('Collision.drawHUD(fighting);', 'Collision.drawStage(fighting);Collision.drawHUD(fighting);');
rep('resourceGate.completed=function(mode)Collision.hudNodes={};', "resourceGate.completed=function(mode)if mode~='battle'then Collision.stagePaintKey=nil;Collision.stageNodes={}end;Collision.hudNodes={};");
function find(n,name){if(n.name===name)return n;for(const c of n.children||[]){const r=find(c,name);if(r)return r;}}
const host=find(save.assets.server.root,'FighterDemo'),proto=find(host,'Art');
// Remove obsolete background geometry from this candidate only; historical saves remain unchanged.
const old=new Set(['Floor','FloorEdge','Sky','Horizon','Backdrop','Mountains']);
host.children=host.children.filter(n=>!old.has(n.name)&&!/^Tile\d+$|^Cap\d+$|^Pillar\d+$/.test(n.name));
for(const name of['BackdropArt','Stage1','Stage2','Stage3']){const n=find(host,name);if(n){n.children=[];n.visible=false;}}
const art=structuredClone(proto);art.id='country_stage_v1';art.name='CountryStage';art.children=[];art.visible=false;art.raycastTarget=false;delete art.scriptMappingIds;
for(const t of Object.values(art.transformByPlatform)){t.offset={x:0,y:0};t.size={x:1,y:1};t.scale={x:1,y:1,z:1};t.anchorMin=t.anchorMax=t.pivot={x:.5,y:.5};}
host.children.push(art);save._pixelJobs.push({path:['CountryStage'],prefix:'StagePx',count:Math.max(...packed.map(f=>f.count))});
save.assets.scripts[0].source=source;write(out+'/base.save.json',JSON.stringify(save));
write(out+'/scene-report.json',JSON.stringify({stageSeedRange:[1,210],source:stageSource,sampling:'nearest',budgetPerScene:stageBudget,countries:keys.map((key,i)=>({key,name:names[i],grid:[frames[i].w,frames[i].h],rectangles:frames[i].rows.length,compressedBytes:packed[i].compressedBytes})),maxCurrentStageImages:Math.max(...packed.map(f=>f.count)),onlyCurrentStageDecoded:true,lossyColorReduction:true,sourceMastersPreserved:true,nativeDeviceVerified:false},null,2));
console.log('COUNTRY_STAGES_READY',packed.map(f=>f.count));
