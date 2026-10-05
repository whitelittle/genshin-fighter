import http from 'node:http';
import {readFileSync} from 'node:fs';
const original=readFileSync('C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/web/dist/public/play-renderer.js','utf8');
const marker='left=p.x>=235&&p.x<=1365&&p.y>=175&&p.y<=725;';
if(!original.includes(marker))throw Error('Renderer pointer mapping changed');
// Route canvas clicks to UI hit testing; J remains the keyboard attack key.
const renderer=original.replace(marker,'left=false;');
http.createServer((req,res)=>{
 if(['/play-renderer.js','/editor/play-renderer.js'].includes(req.url?.split('?')[0])){res.writeHead(200,{'content-type':'text/javascript','cache-control':'no-store'});res.end(renderer);return;}
 const headers={...req.headers,host:'127.0.0.1:4197'};if(headers.origin)headers.origin='http://127.0.0.1:4197';
 const upstream=http.request({hostname:'127.0.0.1',port:4197,path:req.url,method:req.method,headers},r=>{res.writeHead(r.statusCode,r.headers);r.pipe(res);});upstream.on('error',e=>{res.writeHead(502);res.end(e.message);});req.pipe(upstream);
}).listen(4198,'127.0.0.1',()=>console.log('Pointer-corrected demo http://127.0.0.1:4198/editor/play'));
