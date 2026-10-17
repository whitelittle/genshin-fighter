import fs from 'node:fs';import crypto from 'node:crypto';import assert from 'node:assert/strict';
import {decode,encode} from './node-gia-wire.mjs';
const root='outputs/pc-attack-budget-20261014',base='outputs/body-scale-fix-20261013';
const template=fs.readFileSync(base+'/gia/gpt_20261013_同角色尺寸修复_仅脚本.gia'),old=fs.readFileSync(base+'/release/genshin_fighter.lua');
assert.equal(template.readUInt32BE(16),template.length-24);
function patch(fields,from,to){return fields.map(f=>{if(f.w!==2)return f;if(f.v.equals(from)){count++;return {...f,v:to}}try{const a=decode(f.v);if(!encode(a).equals(f.v))return f;const before=count,b=patch(a,from,to);return count===before?f:{...f,v:encode(b)}}catch{return f}})}
function envelope(payload){const h=Buffer.from(template.subarray(0,20));h.writeUInt32BE(payload.length+20,0);h.writeUInt32BE(payload.length,16);return Buffer.concat([h,payload,template.subarray(-4)])}
const original=decode(template.subarray(20,-4));assert(encode(original).equals(template.subarray(20,-4)));let count=0;
fs.mkdirSync(root+'/gia',{recursive:true});const files=[];const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
for(const [variant,label] of [['flash-only','A_仅闪白优化'],['shared-budget','B_闪白与共享绘制预算']]){
 const source=fs.readFileSync(root+'/'+variant+'/genshin_fighter.lua');count=0;
 const changed=envelope(encode(patch(original,old,source)));assert.equal(count,1,'must replace exactly one script source');
 count=0;const restored=envelope(encode(patch(decode(changed.subarray(20,-4)),source,old)));assert.equal(count,1);assert(restored.equals(template),'must preserve all non-source fields');
 const filename='gpt_20261014_PC连续攻击_'+label+'_仅脚本.gia';fs.writeFileSync(root+'/gia/'+filename,changed);files.push({variant,filename,bytes:changed.length,sha256:sha(changed),sourceSha256:sha(source),sourceFieldReplacements:1,reverseByteIdentical:true});
}
fs.writeFileSync(root+'/gia/delivery.json',JSON.stringify({scope:'script-only candidate, unchanged envelope and script identity',protocolVersion:6,nativeImportVerified:false,externalDelivery:false,files},null,2));console.log(JSON.stringify(files));
