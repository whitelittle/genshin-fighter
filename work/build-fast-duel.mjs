import{readFileSync,writeFileSync,mkdirSync}from'node:fs';import assert from'node:assert/strict';
const out='outputs/duel-fast-no-select';mkdirSync(out,{recursive:true});
const save=JSON.parse(readFileSync('outputs/duel-vnext/fighter.save.json'));let source=save.assets.scripts[0].source;
const host=save.assets.server.root.children[0];const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean);
const caps=['keqing','diluc'].map(r=>JSON.parse(readFileSync('assets/vnext/'+r+'-frames.json')).pool);
function rep(a,b){assert.ok(source.includes(a),a);source=source.replace(a,b);}
rep("local menuMode='home'","local menuMode='battle'");rep('local menuReady={false,false}','local menuReady={true,true}');
const selectionStart=source.indexOf('local function sendSelection()'),selectionEnd=source.indexOf('\nlocal function leaveMatch',selectionStart);source=source.slice(0,selectionStart)+'local function sendSelection()end'+source.slice(selectionEnd);
const stageStart=source.indexOf('local function drawStage()'),stageEnd=source.indexOf('\nlocal ',stageStart+25);source=source.slice(0,stageStart)+"local function drawStage()\n if drawnStage==stage then return end\n for n=1,3 do rootNode('Stage'..n):SetVisible(n==stage)end\n drawnStage=stage\nend\n"+source.slice(stageEnd);
rep('local previous=visualCounts[i] or 2335',`local previous=visualCounts[i] or ({${caps}})[i]`);
rep('tonumber(params[5])~=menuEpoch','(tonumber(params[5])or 1)~=menuEpoch');
source=source.replace("rootNode('Restart'):SetVisible(false)","rootNode('Restart'):SetVisible(false);rootNode('Help'):SetVisible(false);rootNode('MotionHelp'):SetVisible(false)\n local mobile=game.GetDevice()==Enum.Device.Mobile or game.GetDevice()==Enum.Device.MobileController\n for _,name in ipairs({'Light','Heavy','Jump','Block','Skill','Ultimate'})do rootNode(name):SetVisible(fighting and mobile)end\n for d=1,9 do rootNode('Stick'..d):SetVisible(fighting and mobile)end");
for(let i=0;i<2;i++){const actor=find(host,i?'Diluc':'Keqing');find(actor,'Sprite').children=find(actor,'Sprite').children.filter(n=>Number(n.name.slice(1))<=caps[i]);if(i===0)find(actor,'Phoenix').children=[];}
for(const name of ['BackdropArt','ChooseKeqingFace','ChooseDilucFace'])find(host,name).children=[];
// No selection relay dependency; seat -> join -> frame relay remains.
save.serverLogic.rules=save.serverLogic.rules.filter(r=>r.id!=='selection');
save.assets.scripts[0].source=source;save.meta.name='固定刻晴迪卢克双人测试';writeFileSync(out+'/base.save.json',JSON.stringify(save));
let runtime=readFileSync('work/duel-loading-runtime.lua','utf8');
runtime=runtime.replace('box:SetVisible(true);box:SetActive(true);box:SetAnchoredPosition(0,0);box:SetSizeDelta(1,1);box:SetAsFirstSibling()',"if loadingParent.name=='Portrait1' or loadingParent.name=='Portrait2' then box:SetAsFirstSibling()end");
runtime=runtime.replace("pixel.name=row[1];pixel:SetAnchoredPosition(row[2],row[3]);pixel:SetSizeDelta(row[4],row[5]);pixel:SetVisible(row[7]==1)","pixel.name=row[1];pixel:SetVisible(false)");
runtime=runtime.replace('pixel.imageColor=Color.FromRGBA(math.floor(c/65536)%256,math.floor(c/256)%256,c%256,math.floor(c/16777216)%256)','');
writeFileSync('work/fast-duel-loading-runtime.lua',runtime);console.log({caps});
