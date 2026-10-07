import fs from 'node:fs';
import http from 'node:http';
import assert from 'node:assert/strict';
import worker from '../dist/server/index.js';
import assets from '../dist/server/assets.js';

for(const url of Object.keys(assets)) {
  const response=await worker.fetch(new Request('https://test.local'+url),{});
  assert.equal(response.status,200,url);
  assert.equal(response.headers.get('Content-Encoding'),null,url);
  assert(Buffer.from(await response.arrayBuffer()).equals(fs.readFileSync('dist'+url)),url);
}
const server=http.createServer(async(req,res)=>{
  const response=await worker.fetch(new Request('http://localhost'+req.url,{method:req.method}),{});
  // Reproduce a proxy which forwards only content type and cache headers.
  res.writeHead(response.status,{'Content-Type':response.headers.get('Content-Type')||'text/plain','Cache-Control':'no-cache'});
  res.end(Buffer.from(await response.arrayBuffer()));
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
try {
  const origin='http://127.0.0.1:'+server.address().port;
  for(const [url,text] of [['/','完整模拟器'],['/actions/nahida/','纳西妲'],['/actions/raiden/','雷电将军']]) {
    const response=await fetch(origin+url);
    const html=await response.text();
    assert(html.startsWith('<!doctype html>')||html.startsWith('<!DOCTYPE html>'),url);
    assert(html.includes(text),url);
    assert(!html.includes('\uFFFD'),url);
  }
  for(const url of ['/actions/nahida/app.js','/actions/raiden/app.js','/editor/bootstrap.js','/projects/raiden-nahida.json']) {
    const response=await fetch(origin+url);
    assert(Buffer.from(await response.arrayBuffer()).equals(fs.readFileSync('dist'+url)),url);
  }
  assert.equal((await fetch(origin+'/projects/raiden-nahida.json')).headers.get('Content-Type'),'application/json');
  assert((await (await fetch(origin+'/projects/raiden-nahida.json')).json()).assets.scripts.length>0);
  assert.equal((await fetch(origin+'/missing')).status,404);
  assert.equal((await fetch(origin+'/',{method:'HEAD'})).status,200);
} finally { await new Promise(resolve=>server.close(resolve)); }
const size=fs.readdirSync('dist/server').reduce((n,x)=>n+fs.statSync('dist/server/'+x).size,0);
assert(size<64*1024*1024,'Worker size limit');
fs.mkdirSync('verification/static-responses-r29',{recursive:true});
fs.writeFileSync('verification/static-responses-r29/report.json',JSON.stringify({release:'r29',assets:Object.keys(assets).length,workerBytes:size,checks:['all resource bytes equal original files','all three UTF-8 entry pages','HTTP without compression headers','both action scripts and simulator bootstrap','project JSON','HEAD and 404'],method:'Production Worker fetch plus local HTTP proxy'},null,2));
console.log('PASS r29: '+Object.keys(assets).length+' exact resources; three readable entry pages; header-independent HTTP; '+size+' Worker bytes');
