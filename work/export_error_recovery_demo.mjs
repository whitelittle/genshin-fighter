import fs from 'node:fs';import assert from 'node:assert/strict';import crypto from 'node:crypto';import {decode,encode} from './node-gia-wire.mjs';
const O='outputs/error-recovery-demo-20261015',base='outputs/error-recovery-20261015';
const old=fs.readFileSync(base+'/release/genshin_fighter.lua'),source=fs.readFileSync(O+'/release/genshin_fighter.lua'),template=fs.readFileSync(base+'/gia/gpt_20261015_V9_报错页退出与重启_仅脚本.gia');
assert.equal(template.readUInt32BE(16),template.length-24);let count=0;
function patch(fields,from,to){return fields.map(f=>{if(f.w!==2)return f;if(f.v.equals(from)){count++;return {...f,v:to}}try{const a=decode(f.v);if(!encode(a).equals(f.v))return f;const before=count,b=patch(a,from,to);return before===count?f:{...f,v:encode(b)}}catch{return f}})}
function env(payload){const h=Buffer.from(template.subarray(0,20));h.writeUInt32BE(payload.length+20,0);h.writeUInt32BE(payload.length,16);return Buffer.concat([h,payload,template.subarray(-4)])}
const output=env(encode(patch(decode(template.subarray(20,-4)),old,source)));assert.equal(count,1);count=0;const reversed=env(encode(patch(decode(output.subarray(20,-4)),source,old)));assert.equal(count,1);assert(reversed.equals(template));
const filename='gpt_20261015_V9_主动报错按钮演示_测试专用_仅脚本.gia';fs.mkdirSync(O+'/gia',{recursive:true});fs.writeFileSync(O+'/gia/'+filename,output);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');fs.writeFileSync(O+'/gia/delivery.json',JSON.stringify({filename,bytes:output.length,sha256:sha(output),sourceSha256:sha(source),reverseTemplateByteIdentical:true,protocolVersion:8,nativeDeviceVerified:false,externalDelivery:false},null,2));console.log(filename);
