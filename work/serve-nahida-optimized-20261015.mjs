import fs from 'node:fs';
import {createServer} from 'node:http';
const out='outputs/nahida-native-optimized-20261015';
const html=`<!doctype html><html lang="zh"><meta charset="utf-8"><title>草神 · 基础图元自动优化试验</title><style>body{margin:0;background:#f5f3ed;color:#354139;font:16px system-ui}header,p{padding:12px 24px}a{color:#286645;margin-right:20px}img{display:block;margin:auto;width:min(100%,1600px)}#comparison{width:min(100%,1200px)}</style><header><b>基础图元自动优化试验 · 209图元</b><p><a href="/result.gia" download="草神_209基础图元拼装.gia">下载GIA</a><a href="/result.svg" download="草神_209图元优化.svg">下载SVG</a><a href="http://127.0.0.1:8822/">上版249图元</a></p></header><p>只调整已有图元的位置、大小、旋转和颜色，并移除贡献小的图元。249→209；主体色彩误差55.59→31.423；轮廓交并比72.04%→90.39%。轮廓交并比不是整体相似度。五官、描边和部件接缝仍有失真，本版未达高还原验收，真机未验证。</p><img id="comparison" src="/comparison.png" alt="参考、原版、优化版对照"><p>下图为实际GIA回读的模拟器显示：</p><img src="/screen.png" alt="实际GIA模拟器结果"></html>`;
createServer((req,res)=>{
 if(req.url==='/'){res.writeHead(200,{'content-type':'text/html;charset=utf-8'});res.end(html);return;}
 const routes={'/result.gia':['草神_209基础图元拼装.gia','application/octet-stream'],'/result.svg':['optimized.svg','image/svg+xml'],'/comparison.png':['comparison.png','image/png'],'/screen.png':['actual-gia-simulator.png','image/png'],'/state':['verification.json','application/json']};
 const item=routes[req.url];if(!item){res.writeHead(404);res.end();return;}
 res.writeHead(200,{'content-type':item[1],'cache-control':'no-store'});fs.createReadStream(out+'/'+item[0]).pipe(res);
}).listen(8823,'127.0.0.1',()=>console.log('http://127.0.0.1:8823/'));
