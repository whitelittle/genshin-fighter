import{readFileSync,writeFileSync,existsSync}from'node:fs';
import{createHash}from'node:crypto';
const read=p=>readFileSync(p,'utf8'),put=(p,s)=>writeFileSync(p,s,'utf8');
const scene='work/build-pixel-country-scenes.mjs';put(scene,read(scene).replaceAll('最近邻5000档','最近邻${budget}档'));
const doc='docs/current/技术实现与验证.md';put(doc,read(doc).replace('Frames透传Slot/FirstFrame/AckFrame/Payload','Frames透传Slot/FirstFrame/AckFrame/Payload/Epoch'));
const check='docs/修复进度与验收清单_20261004.md';const current='> 当前修订：20261004_143008包已使用9000档七背景、19角色、绫华56姿势与逐帧ROI、防御快照和头像下蓝红圆点。具体证据与未完成项见 [问题台账](current/问题台账.md)。下文5000档/未接入绫华为历史阶段，不能作为当前状态。\n\n';put(check,current+read(check));
const files=['outputs/midphase-final/verification.json','outputs/midphase-final/collision-verification.json','outputs/midphase-final/loading-verification.json','outputs/midphase-final/mobile-verification.json'];for(const p of files)JSON.parse(read(p));
const delivery=JSON.parse(read('outputs/midphase-final/delivery.json'));
for(const f of delivery.files){const hash=createHash('sha256').update(readFileSync('outputs/midphase-final/'+f.filename)).digest('hex');if(hash!==f.sha256)throw Error('Delivery hash mismatch: '+f.filename);}
const indexPath='docs/current/有效资源索引.json';const index=JSON.parse(read(indexPath));
for(const p of ['work/build-pixel-country-scenes.mjs','work/finish-midphase-records.mjs'])if(existsSync(p))index.resources.push({path:p,bytes:readFileSync(p).length,sha256:createHash('sha256').update(readFileSync(p)).digest('hex')});
put(indexPath,JSON.stringify(index,null,2));
console.log('Delivery hashes verified; four verification reports parse; current documents and source labels aligned. No files deleted.');
