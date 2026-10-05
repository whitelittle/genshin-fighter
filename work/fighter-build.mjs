import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import {validateServerGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const out='outputs/fighter-v0.5';mkdirSync(out,{recursive:true});
const save=JSON.parse(readFileSync('C:/Users/Cheng/Documents/ChatGPT/嘟嘟可大冒险/outputs/animation-probe/animation-probe.save.json'));
const host=save.assets.server.root.children[0],template=host.children.find(n=>n.name==='Actor'),pixel=template.children[0],label=host.children.find(n=>n.name==='Help'),button=host.children.find(n=>n.name==='Replay');
host.children=[];host.name='FighterDemo';host.showCursor=true;host.active=true;host.disableKeyEventPassthrough=true;
let seq=0,guid=1099100000;
function node(t,name,x,y,w,h,parent){const n=structuredClone(t);n.id='fighter_'+(++seq);n.guid=guid++;n.name=name;n.children=[];delete n.scriptMappingIds;delete n.giaRelatedGuids;n.active=true;n.visible=true;n.raycastTarget=false;for(const a of Object.values(n.transformByPlatform)){a.offset={x,y};a.size={x:w,y:h};a.scale={x:1,y:1,z:1};a.rotation={x:0,y:0,z:0};a.anchorMin=a.anchorMax={x:.5,y:.5};a.pivot={x:.5,y:.5};}parent.children.push(n);return n;}
const group=(name,x,y,p=host)=>node(template,name,x,y,1,1,p);
function rect(name,x,y,w,h,c,p=host){const n=node(pixel,name,x,y,w,h,p);n.imageId=100001;n.imageColor=Number('0xff'+c)>>>0;return n;}
function text(name,s,x,y,w=500,p=host){const n=node(label,name,x,y,w,32,p);n.text=s;n.fontSize=20;return n;}
function btn(name,s,x,y,w=100){const n=node(button,name,x,y,w,42,host);n.raycastTarget=true;const tx=node(label,name+'Text',0,0,w,40,n);tx.text=s;tx.fontSize=18;}
rect('Backdrop',0,0,1280,720,'131b30');rect('Horizon',0,-85,1280,245,'202d48');
for(let i=0;i<9;i++){rect('Pillar'+i,-600+i*150,-5,28,220,'293954');rect('Cap'+i,-600+i*150,109,50,8,'455776');}
rect('Floor',0,-205,1280,90,'35405a');rect('FloorEdge',0,-158,1280,6,'b4bbc9');
for(let i=0;i<16;i++)rect('Tile'+i,-600+i*80,-205,2,90,'202b44');
const skins=['ffe1cd','ffddc1'];
function fighter(name,isDiluc){const a=group(name,isDiluc?240:-240,-155);const art=group('Art',0,0,a),hair=isDiluc?'bd3930':'aa91da',body=isDiluc?'252834':'644696',trim=isDiluc?'b9955b':'e6cf8a';
 rect('Tail',-26,148,14,isDiluc?62:85,hair,art);if(!isDiluc)rect('TwinTail',-40,128,12,91,'8871be',art);
 const back=group('BackLeg',-15,65,art),front=group('FrontLeg',14,65,art);
 for(const [p,c] of [[back,'272432'],[front,isDiluc?'333640':'413341']]){rect('Leg',0,-22,14,58,c,p);rect('Boot',6,-55,27,13,isDiluc?'252a37':'614490',p);}
 rect('Coat',-12,84,42,isDiluc?69:40,body,art);rect('Torso',0,123,43,59,body,art);rect('Chest',10,135,13,31,isDiluc?'d7d3cc':'cbb9ea',art);rect('Gold',7,111,30,5,trim,art);rect('Neck',3,161,13,17,skins[isDiluc?1:0],art);
 rect('Face',6,180,28,34,skins[isDiluc?1:0],art);rect('Hair',-2,197,39,18,hair,art);rect('Bangs',16,190,12,18,hair,art);rect('Eye',17,182,4,4,isDiluc?'d9584b':'7250a7',art);
 if(!isDiluc){rect('Bun1',-13,211,12,17,hair,art);rect('Bun2',10,207,10,14,hair,art);rect('Flower',12,199,7,7,trim,art);}
 const arm=group('Arm',17,135,art);rect('Forearm',18,-8,39,13,isDiluc?'363945':'ffe1cd',arm);rect('Glove',36,-8,12,15,body,arm);
 const sword=group('Sword',50,124,art);rect('Grip',5,0,20,7,'55414d',sword);rect('Guard',19,0,7,23,trim,sword);rect('Blade',isDiluc?72:64,0,isDiluc?103:84,isDiluc?20:8,isDiluc?'3b3540':'dce3f3',sword);if(isDiluc)rect('RedEdge',72,5,101,5,'c23c3d',sword);else rect('SwordEdge',64,2,84,2,'a78ee8',sword);
 const fx=group('SpecialFx',100,95,a);for(let i=0;i<7;i++)rect('Streak'+i,20+i*16,-30+i*10,60,4,isDiluc?(i%2?'ffc64d':'ff792d'):(i%2?'d6c9ff':'9b75ee'),fx);
 rect('Flash',0,110,60,180,'ffaaaa',a);rect('GuardVisual',46,115,5,100,isDiluc?'ffa45b':'bdb7ff',a);rect('Hitbox',110,120,120,4,isDiluc?'ff994c':'d8b6ff',a);return a;
}
fighter('Keqing',false);fighter('Diluc',true);
rect('HpBack1',-325,264,490,25,'101524');rect('Hp1',-325,264,480,19,'ac8aed');rect('HpBack2',325,264,490,25,'101524');rect('Hp2',325,264,480,19,'e97854');
text('Name1','刻晴',-325,300);text('Name2','迪卢克 / 电脑',325,300);text('Timer','60',0,294,100);text('Status','第 1 回合',0,221,1100);text('Stats','',0,-278,1200);
text('Combo1','',-360,192);text('Combo2','',360,192);text('State1','',-360,162);text('State2','',360,162);
text('Help','A/D 移动 | S+J 下段 | J,J,K 连段 | 空格 跳跃 | L 站防 | S+L 蹲防 | 236+J/K 必杀 | 623+K 挑飞 | R 重开',0,-317,1200).fontSize=17;text('ArtNote','原神格斗原型 v0.5 / 挑飞 · 空中追击 · 搓招',0,338,1200).fontSize=14;
for(const [n,s,x] of [['Left','向左',-540],['Right','向右',-420],['Down','蹲下',-300],['Jump','跳跃',-180],['Light','快剑',120],['Heavy','上段重击',240],['Block','防御',480],['Restart','重开',-60]])btn(n,s,x,-235);
function reverse(n){n.children.reverse();for(const c of n.children)reverse(c);}reverse(host);
const source=readFileSync('work/fighter.lua','utf8');save.assets.scripts=[{id:String(guid),guid:guid++,path:'lua/fighter.lua',source,controlId:host.id,controlAsset:''}];save.meta.name='刻晴对迪卢克 v0.5';
writeFileSync(out+'/fighter.lua',source);writeFileSync(out+'/fighter.save.json',JSON.stringify(save));
const ex=createStudio(save).exportData('gia-combined');const buffer=Buffer.from(ex.data,ex.encoding),v=validateServerGiaCompatibility(buffer);if(!v.valid)throw Error(JSON.stringify(v));writeFileSync(out+'/gpt_fighter_v0.5.gia',buffer);
writeFileSync(out+'/build.json',JSON.stringify({nodes:seq,bytes:buffer.length,giaCompatible:true,art:'program-drawn placeholders',simulatorVerified:false,deviceVerified:false},null,2));console.log(JSON.stringify({nodes:seq,bytes:buffer.length}));
