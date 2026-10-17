import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const profile=process.argv[2]||'light';
const sets=['keqing','diluc'].map(r=>JSON.parse(readFileSync(`assets/demo/${r}-${profile}-frames.json`)));
const sprites=sets.map(a=>a.frames[0]);
const poolSize=Math.max(...sets.map(a=>a.pool));
const luaData='{'+sets.map(set=>'{'+set.frames.map(a=>`{scale=${a.scale},anchor={${a.anchor}},rows={${a.rows.map(([x,y,w,h,r,g,b,alpha])=>`{${x},${y},${w},${h},${((alpha<<24)|(r<<16)|(g<<8)|b)>>>0}}`).join(',')}}}`).join(',')+'}').join(',')+'}';
for(const online of [false,true]){
 const out=`outputs/demo-${online?'online':'solo'}-${profile}`;mkdirSync(out,{recursive:true});
 const save=JSON.parse(readFileSync(online?'outputs/fighter-online-v0.1/fighter-online.save.json':'outputs/fighter-v0.5/fighter.save.json'));
 const host=save.assets.server.root.children[0];
 const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean);
 const pixel=structuredClone(find(host,'Hp1')),label=structuredClone(find(host,'Status')),button=structuredClone(find(host,'Light')),group=structuredClone(find(host,'Art'));
 let seq=0,guid=1180000000;
 function add(t,name,x,y,w,h,p=host,front=true){const n=structuredClone(t);n.id='demo_'+(++seq);n.guid=guid++;n.name=name;n.children=[];n.active=true;n.visible=true;n.raycastTarget=false;delete n.scriptMappingIds;delete n.giaRelatedGuids;
  for(const a of Object.values(n.transformByPlatform)){a.offset={x,y};a.size={x:w,y:h};a.scale={x:1,y:1,z:1};a.rotation={x:0,y:0,z:0};a.anchorMin=a.anchorMax={x:.5,y:.5};a.pivot={x:.5,y:.5};}front?p.children.unshift(n):p.children.push(n);return n;
 }
 const box=(name,x,y,w,h,c,p=host,front=true)=>{const n=add(pixel,name,x,y,w,h,p,front);n.imageColor=Number('0xff'+c)>>>0;return n;};
 const tx=(name,text,x,y,w=400,p=host)=>{const n=add(label,name,x,y,w,28,p);n.text=text;n.fontSize=15;return n;};
 const btn=(name,text,x,y,w=110,h=40)=>{const n=add(button,name,x,y,w,h);n.raycastTarget=true;tx(name+'Text',text,0,0,w,n).fontSize=16;return n;};
 // Replace the complete placeholder artwork with one reusable rectangle pool per fighter.
 for(let i=0;i<2;i++){const actor=find(host,i?'Diluc':'Keqing'),art=actor.children.find(n=>n.name==='Art');art.children=[];
  const flash=actor.children.find(n=>n.name==='Flash'),spark=structuredClone(group);spark.id=flash.id;spark.guid=flash.guid;spark.name='Flash';spark.children=[];spark.visible=false;for(const t of Object.values(spark.transformByPlatform)){t.offset={x:0,y:115};t.size={x:1,y:1};}actor.children[actor.children.indexOf(flash)]=spark;
  box('SparkH',0,0,44,5,'ffebb5',spark);box('SparkV',0,0,5,44,'ffebb5',spark);box('SparkCenter',0,0,14,14,'ffffff',spark);
  const pool=add(group,'Sprite',0,0,1,1,art);const a=sprites[i];
  for(let n=0;n<poolSize;n++){const r=a.rows[n];const p=box('P'+(n+1),r?(r[0]+r[2]/2-a.anchor[0])*a.scale:0,r?(a.anchor[1]-r[1]-r[3]/2)*a.scale:0,r?r[2]*a.scale:1,r?r[3]*a.scale:1,'ffffff',pool);p.visible=!!r;if(r)p.imageColor=((r[7]<<24)|(r[4]<<16)|(r[5]<<8)|r[6])>>>0;}
 }
 for(const n of host.children){if(/^(Backdrop|Horizon|Pillar|Cap|Floor|Tile)/.test(n.name))n.visible=false;if(['Left','Right','Down','ArtNote'].includes(n.name))n.visible=false;}
 // Three recognizable block-art stage layouts; final background paintings remain a later asset pass.
 for(let stage=1;stage<=3;stage++){
  const p=add(group,'Stage'+stage,0,0,1,1,host,false);p.visible=stage===1;
  box('Sky',0,0,1280,720,stage===3?'273441':'77adbc',p,false);
  for(let n=0;n<8;n++)box('Hill'+n,-540+n*154,-40,200,180+(n%3)*55,stage===3?'394c50':'608d79',p);
  if(stage===1){box('Trunk',80,20,100,300,'574e3c',p);for(let n=0;n<13;n++)box('Canopy'+n,80+Math.sin(n*1.7)*260,145+Math.cos(n*.8)*70,190,90,n%2?'3b6d59':'4e8063',p);for(let n=0;n<8;n++)box('Roots'+n,80+(n-4)*28,-120,40,40+n%3*18,'625d46',p);}
  else if(stage===2){box('Wall',0,0,760,270,'969c99',p);box('Gate',0,-35,140,190,'435462',p);for(const x of [-440,440]){box('Tower',x,25,160,330,'afb3a7',p);box('Roof',x,195,195,22,'395a78',p);}for(let n=0;n<17;n++)box('Battlement'+n,-570+n*70,170,36,50,'adb1a5',p);}
  else {for(let n=0;n<7;n++){box('Ruin'+n,-500+n*180,15,48,150+(n%3)*75,'697570',p);box('RuinCap'+n,-500+n*180,100+(n%3)*37,90,28,'829086',p);}box('BrokenArch',0,120,230,34,'6c7976',p);}
  box('Ground',0,-217,1280,118,stage===1?'6a7953':'7d827b',p);box('GroundLine',0,-158,1280,5,'c5c7ae',p);
  for(let n=0;n<15;n++)box('Paving'+n,-600+n*88,-216,2,110,'555e55',p);
 }
 const panel=box('TopPanel',0,290,1240,110,'151923',host,false);host.children.pop();host.children.splice(host.children.findIndex(n=>n.name==='Stage1'),0,panel);
 box('MeterBack1',-325,245,490,12,'171d29');box('MeterBack2',325,245,490,12,'171d29');box('Meter1',-565,245,1,8,'9b79eb');box('Meter2',565,245,1,8,'f08749');
 tx('Energy1','',-325,232);tx('Energy2','',325,232);tx('StageTitle','风起地 · 大树前',0,190,420);
 btn('RoleKeqing','选择刻晴',-505,338);btn('RoleDiluc','选择迪卢克',-385,338);
 for(let n=1;n<=3;n++)btn('SelectStage'+n,['风起地','蒙德大桥','风龙废墟'][n-1],230+(n-1)*125,338,118);
 const arrows=['↙','↓','↘','←','●','→','↖','↑','↗'];
 for(let d=1;d<=9;d++)btn('Stick'+d,arrows[d-1],-480+((d-1)%3-1)*48,-232+(Math.floor((d-1)/3)-1)*48,46,46);
 for(const [name,x,text] of [['Light',185,'轻攻击'],['Heavy',295,'重攻击'],['Block',515,'防御'],['Jump',405,'跳跃'],['Restart',-80,'重开']]){const n=find(host,name);for(const a of Object.values(n.transformByPlatform)){a.offset={x,y:-248};a.size={x:100,y:64};}n.children[0].text=text;}
 find(host,'Help').text='A/D 移动 · S 蹲下 · 空格 跳跃 · J 轻攻 · K 重攻 · 前+K 上段 · S+J 下段 · L 防御';find(host,'Help').fontSize=15;
 tx('MotionHelp','236+J/K 必杀 · 623+K 挑飞 · 236236+K 超必杀（100能量） · 左侧摇杆可拖动搓招',0,-341,1200).fontSize=15;
 find(host,'Stats').fontSize=14;for(const t of Object.values(find(host,'Stats').transformByPlatform)){t.offset.y=-294;t.size.y=24;}
 const source=readFileSync(online?'work/demo-online.lua':'work/demo-solo.lua','utf8').replace('SPRITE_DATA',luaData).replace('SPRITE_POOL',String(poolSize));
 save.assets.scripts[0].source=source;save.meta.name='原神格斗 Demo · '+(online?'双人联机':'单人AI')+' · '+profile;
 writeFileSync(out+'/fighter.lua',source);writeFileSync(out+'/fighter.save.json',JSON.stringify(save));
 const ex=createStudio(save).exportData('gia-combined'),buffer=Buffer.from(ex.data,ex.encoding),valid=validateServerGiaCompatibility(buffer);if(!valid.valid)throw Error(JSON.stringify(valid));
 writeFileSync(out+`/原神格斗_${online?'双人联机':'单人AI'}_${profile}.gia`,buffer);
 if(online)writeFileSync(out+'/server-logic.json',JSON.stringify(save.serverLogic,null,2));
 writeFileSync(out+'/build.json',JSON.stringify({profile,online,nodesAdded:seq,poolPerFighter:poolSize,residentSpriteImages:poolSize*2,visibleSpriteImages:sprites.reduce((n,a)=>n+a.rows.length,0),giaBytes:buffer.length,giaCompatible:true,serverLogicIncludedInGia:false,sourceArt:'existing character masters and action sheets, sampled and quantized',animation:'four full-figure key poses per role; shared reusable pool',deviceVerified:false},null,2));
 console.log(JSON.stringify({out,poolSize,bytes:buffer.length}));
}
