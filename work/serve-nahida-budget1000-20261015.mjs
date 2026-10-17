import fs from 'node:fs';
import {createServer} from 'node:http';
const out='outputs/nahida-native-budget1000-20261015';
const html=`<!doctype html><html lang="zh"><meta charset="utf-8"><title>草神 · 1000图元预算</title><style>body{margin:0;background:#f5f3ed;color:#354139;font:16px system-ui}header,p{padding:12px 24px}a{color:#286645;margin-right:20px}img{display:block;margin:auto;width:min(100%,1600px)}#comparison{width:min(100%,1200px)}</style><header><b>1000图元预算试验 · 实际994个角色图元</b><p><a href="/result.gia" download="草神_994基础图元拼装.gia">下载GIA</a><a href="/result.svg" download="草神_994图元.svg">下载SVG</a><a href="http://127.0.0.1:8825/">497图元版</a></p></header><p>497→994个角色图片图元；主体色彩误差19.893→15.053，降低约24.3%。轮廓交并比95.99%→96.88%，这个指标不等于整体相似度。五官、发丝、金色饰边仍有明显差异，未达到高还原验收。去除了冗余细节容器，具体总控件见验证记录；真机未验证。</p><img id="comparison" src="/comparison.png" alt="高清参考与218及497图元对比"><p>实际GIA回读模拟器：</p><img src="/screen.png" alt="994图元实际模拟器显示"></html>`;
createServer((req,res)=>{
 if(req.url==='/'){res.writeHead(200,{'content-type':'text/html;charset=utf-8'});res.end(html);return;}
 const routes={'/result.gia':['草神_994基础图元拼装.gia','application/octet-stream'],'/result.svg':['optimized.svg','image/svg+xml'],'/comparison.png':['comparison.png','image/png'],'/screen.png':['actual-gia-simulator.png','image/png'],'/state':['verification.json','application/json']};
 const item=routes[req.url];if(!item){res.writeHead(404);res.end();return;}
 res.writeHead(200,{'content-type':item[1],'cache-control':'no-store'});fs.createReadStream(out+'/'+item[0]).pipe(res);
}).listen(8826,'127.0.0.1',()=>console.log('http://127.0.0.1:8826/'));
