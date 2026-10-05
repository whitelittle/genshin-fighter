import fs from 'node:fs';
import assert from 'node:assert/strict';
import {exportGia,importGia,validateGiaCompatibility} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
// C v1 imported fine but every row was hidden, empty and 2000x1700, so the editor canvas showed nothing.
// Rows are visible placeholders laid out like a grid; runtime code hides, resizes and repositions them on creation.
const latest=JSON.parse(fs.readFileSync('work/training-room-runtime-text-latest.json'));
const save=JSON.parse(fs.readFileSync(latest.out+'/simulator.save.json'));
const find=(n,name)=>n.name===name?n:(n.children||[]).map(c=>find(c,name)).find(Boolean);
const old=find(save.assets.client.root,'StageTextTemplate')||save.assets.client.root.children.find(n=>(n.children||[]).some(c=>c.name==='TextArt1'));
assert(old&&old.children.length===16);
const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date()).map(v=>[v.type,v.value]));
const stamp=p.year+p.month+p.day+'_'+p.hour+p.minute+p.second,cName='gpt_'+stamp+'_训练室文字模板C2';
const template=structuredClone(old);template.name=cName;template.guid=1079100001;
for(const t of Object.values(template.transformByPlatform)){t.size={x:480,y:160};t.offset={x:0,y:0};}
template.children.forEach((n,i)=>{n.visible=true;n.text='T'+(i+1);n.guid=1079100002+i;n.giaRelatedGuids=[];n.scriptMappingIds=[];for(const t of Object.values(n.transformByPlatform)){t.size={x:110,y:36};t.offset={x:(i%4)*120-180,y:60-Math.floor(i/4)*40};}});
const client=structuredClone(save.assets.client);client.root.guid=1079100000;client.root.name=cName;client.root.children=[template];client.meta={...client.meta,name:cName,giaFileName:cName+'.gia',giaFileId:1079100000};
const c=exportGia(client);assert(validateGiaCompatibility(c.buffer).valid);
const back=importGia(c.buffer,cName+'.gia');const t=(back.clientProject||back.project).root.children[0];
assert.equal(t.name,cName);assert.equal(t.children.length,16);assert(t.children.every((n,i)=>n.name==='TextArt'+(i+1)&&n.visible!==false&&n.kind==='textbox'));
fs.writeFileSync(latest.out+'/'+cName+'.gia',c.buffer);
save.assets.client.root.children=save.assets.client.root.children.filter(n=>n!==old&&n.name!==old.name).concat([t]);
fs.writeFileSync(latest.out+'/simulator.save.json',JSON.stringify(save));
fs.writeFileSync('work/training-room-runtime-text-latest.json',JSON.stringify({...latest,cName,cPrevious:latest.cName},null,2));
console.log(JSON.stringify({out:latest.out,cName,bytes:c.buffer.length}));
