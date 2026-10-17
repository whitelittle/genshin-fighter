import fs from 'node:fs';
import {createServer} from 'node:http';
const out='outputs/nahida-native-precision2-20261015';
const html=`<!doctype html><html lang="zh"><meta charset="utf-8"><title>草神 · 精度二档</title><style>body{margin:0;background:#f5f3ed;color:#354139;font:16px system-ui}header,p{padding:12px 24px}a{color:#286645;margin-right:20px}img{display:block;margin:auto;width:min(100%,1600px)}#comparison{width:min(100%,1200px)}</style><header><b>基础图元 · 精度二档 · 218图元</b><p><a href="/result.gia" download="草神_218基础图元拼装.gia">下载GIA</a><a href="/result.svg" download="草神_218图元精度二档.svg">下载SVG</a><a href="http://127.0.0.1:8823/">上一档209图元</a></p></header><p>209→218个角色图片图元。主体色彩误差31.423→28.205，降低约10.2%；轮廓交并比90.39%→94.20%。轮廓交并比不是整体相似度；五官和描边仍有失真。实际GIA回读验证通过，真机未验证。</p><img id="comparison" src="/comparison.png" alt="高清参考与两个精度档位对照"><p>实际GIA回读模拟器：</p><img src="/screen.png" alt="精度二档实际模拟器显示"></html>`;
createServer((req,res)=>{
 if(req.url==='/'){res.writeHead(200,{'content-type':'text/html;charset=utf-8'});res.end(html);return;}
 const routes={'/result.gia':['草神_218基础图元拼装.gia','application/octet-stream'],'/result.svg':['optimized.svg','image/svg+xml'],'/comparison.png':['comparison.png','image/png'],'/screen.png':['actual-gia-simulator.png','image/png'],'/state':['verification.json','application/json']};
 const item=routes[req.url];if(!item){res.writeHead(404);res.end();return;}
 res.writeHead(200,{'content-type':item[1],'cache-control':'no-store'});fs.createReadStream(out+'/'+item[0]).pipe(res);
}).listen(8824,'127.0.0.1',()=>console.log('http://127.0.0.1:8824/'));
