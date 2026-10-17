import{readFileSync,writeFileSync}from'node:fs';
const tree=JSON.parse(readFileSync('outputs/network-node-inspection/wire-tree.json'));
const m=(a,n)=>a.find(f=>f.field===n)?.value?.message||[],v=(a,n)=>a.find(f=>f.field===n)?.value;
function compact(a){return a.map(f=>[f.field,f.value?.message?compact(f.value.message):f.value]);}
const graph=m(m(m(m(tree,1),13),1),1);
const nodes=graph.filter(f=>f.field===3).map(f=>compact(f.value.message));
const result={graphFields:graph.map(f=>f.field),nodes};writeFileSync('outputs/network-node-inspection/node-structures.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
