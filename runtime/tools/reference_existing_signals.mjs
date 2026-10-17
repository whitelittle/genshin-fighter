// Same-map update: retain existing signal resource IDs, omit resource declarations.
// Input must be a corrected export of the current target map, never a generated-ID graph.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {decode,encode,msg,num,str,all} from '../../work/node-gia-wire.mjs';
const args=process.argv.slice(2);
const arg=name=>args[args.indexOf(name)+1];
const input=arg('--input'),output=arg('--out');
assert(input&&output,'Required: --input corrected-current-export.gia --out output.gia');
assert(!fs.existsSync(output),'Refuse overwriting output');
const bytes=fs.readFileSync(input),root=decode(bytes.subarray(20,-4));
const graph=msg(msg(msg(msg(root,1),13),1),1);
const definitions=new Map(all(root,2).map(field=>{
 const unit=decode(field.v),meta=msg(msg(msg(msg(unit,14),1),1),107);
 const name=[101,102,108].map(k=>str(msg(meta,k),1)).find(Boolean);
 return [num(msg(unit,1),4),{name,kind:str(unit,3)}];
}));
const required=new Map();
for(const field of all(graph,3)) {
 const node=decode(field.v),id=num(msg(node,2),5),definition=definitions.get(id);
 if(!definition)continue;
 assert(/^GF3/.test(definition.name)||(args.includes('--keep-imported-names')&&/^信号_\d+$/.test(definition.name)),'Expected GF3 input or explicit imported-name mode');
 required.set(id,definition);
}
assert.equal(new Set([...required.values()].map(d=>d.name)).size,12,'All GF3 signals required');
const resultRoot=root.filter(field=>field.f!==2),payload=encode(resultRoot);
const header=Buffer.from(bytes.subarray(0,20));
header.writeUInt32BE(payload.length+20,0);header.writeUInt32BE(payload.length,16);
const result=Buffer.concat([header,payload,bytes.subarray(-4)]);
const after=decode(result.subarray(20,-4));
assert.equal(all(after,2).length,0);
assert(encode(msg(after,1)).equals(encode(msg(root,1))),'Node graph altered');
fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,result);
const report={filename:path.basename(output),sourceFilename:path.basename(input),sha256:crypto.createHash('sha256').update(result).digest('hex'),embeddedSignalDefinitions:0,sameMapOnly:true,requiredExistingSignals:[...required].map(([id,definition])=>({id,...definition})),graphUnchanged:true,nativeImportVerified:false};
fs.writeFileSync(output+'.json',JSON.stringify(report,null,2));
console.log(JSON.stringify({embeddedSignalDefinitions:0,signalNames:12,resourceReferences:required.size,sameMapOnly:true,graphUnchanged:true,nativeImportVerified:false}));
