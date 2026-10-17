// Reuse the existing wire interpreter with the map's GFV2 declarations.
import fs from 'node:fs';import path from 'node:path';import {pathToFileURL} from 'node:url';
const source=fs.readFileSync(path.join(import.meta.dirname,'verify_team_native.mjs'),'utf8');
const core=source.slice(0,source.indexOf('const checks=[];'));
const checks=`
const checks=[];
let x=receive('GFV2Hello');
assert.deepEqual(x.map(o=>[o.signal,o.target,o.params.Slot]),[['GFV2Seat',301,1],['GFV2Seat',502,2]]);
checks.push('Hello uses both players and seats 1/2');
const payload='GFV2:-7201,123,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0';
const packet={Slot:1,Sequence:4,Ack:2,Payload:payload,Epoch:1};
x=receive('GFV2Frames',packet);assert.equal(x.length,1);assert.equal(x[0].signal,'GFV2FramesOut');assert.equal(x[0].target,502);assert.deepEqual(x[0].params,packet);
x=receive('GFV2Frames',{...packet,Slot:2});assert.equal(x.length,1);assert.equal(x[0].target,301);assert.equal(x[0].params.Payload,payload);
checks.push('Both directions preserve all five fields and the exact string');
assert.equal(receive('GFV2Frames',{...packet,Slot:3}).length,0);
assert.equal(receive('GFV2Frames',{...packet,Epoch:2}).length,0);
checks.push('Invalid slot and epoch reject');
players.splice(1);x=receive('GFV2Hello');assert.equal(x.length,1);assert.equal(x[0].params.Slot,1);
assert.equal(receive('GFV2Frames',packet).length,0);
checks.push('One-player seat and absent second-player guard');
const report={checks,nodes:nodes.size,sha256:crypto.createHash('sha256').update(b).digest('hex'),nativeImportVerified:false};
fs.writeFileSync(out+'/gfv2-native-verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
`;
const temporary=path.join(import.meta.dirname,'../../work/gfv2-wire-verifier-20261013.mjs');
// The interpreter's utility import is relative to runtime/tools.
fs.writeFileSync(temporary,(core+checks).replace("from'../../work/node-gia-wire.mjs'","from'./node-gia-wire.mjs'"));
await import(pathToFileURL(temporary).href);
