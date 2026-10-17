import {createServer} from 'node:http';
import fs from 'node:fs';
const out='outputs/nahida-native-collage-20261014';
const html=`<!doctype html><html lang="zh"><meta charset="utf-8"><title>草神 · 基础图元拼装</title><style>body{margin:0;background:#f5f3ed;color:#354139;font:16px system-ui}header{padding:16px 24px;display:flex;gap:18px;align-items:center;flex-wrap:wrap}a{color:#286645}button{padding:6px 12px}img{display:block;width:min(100%,1600px);margin:auto}p{padding:0 24px}#comparison{display:none;width:min(100%,880px)}</style><header><b>草神 · 基础图元拼装小样</b><a href="/collage.gia" download="草神_249基础图元拼装.gia">下载 GIA</a><a href="/collage.svg" download="草神_249基础图元拼装.svg">下载 SVG</a><button onclick="document.querySelector('#comparison').style.display=document.querySelector('#comparison').style.display==='block'?'none':'block'">参考图对照</button></header><p>249个角色图片图元：165个椭圆、47个三角形、30个矩形、7个四角星。按发束、五官、身体与服装部件叠放；轮廓和细节仍有差异。GIA约237 KB，已回读核对图元、尺寸、旋转和颜色；真机未验证。</p><img id="comparison" src="/comparison.png" alt="高清第一帧与拼装小样对比"><img src="/screen.png" alt="实际GIA回读模拟器显示"></html>`;
createServer((req,res)=>{
 const entries={'/screen.png':['actual-gia-simulator.png','image/png'],'/comparison.png':['comparison.png','image/png'],'/collage.gia':['草神_249基础图元拼装.gia','application/octet-stream'],'/collage.svg':['collage.svg','image/svg+xml'],'/state':['verification.json','application/json']};
 if(req.url==='/'){res.writeHead(200,{'content-type':'text/html;charset=utf-8'});res.end(html);return;}
 const entry=entries[req.url];if(!entry){res.writeHead(404);res.end();return;}
 res.writeHead(200,{'content-type':entry[1],'cache-control':'no-store'});fs.createReadStream(out+'/'+entry[0]).pipe(res);
}).listen(8822,'127.0.0.1',()=>console.log('http://127.0.0.1:8822/'));
