import {createServer} from 'node:http';
import fs from 'node:fs';
const out='outputs/nahida-18color-native-gia-20261014';
const html=`<!doctype html><html lang="zh"><meta charset="utf-8"><title>草神 GIA · 模拟器转换试验</title><style>body{margin:0;background:#f5f3ed;font:16px system-ui;color:#354139}header{padding:16px 24px;display:flex;gap:18px;align-items:center;flex-wrap:wrap}a{color:#286645}button{padding:6px 12px}img{display:block;width:min(100%,1600px);margin:auto}p{padding:0 24px}#original{display:none;height:680px;width:auto}</style><header><b>草神18色版 · GIA转换试验</b><a href="/study.gia" download="草神_18色矢量几何实验.gia">下载 GIA</a><button onclick="document.querySelector('#original').style.display=document.querySelector('#original').style.display==='block'?'none':'block'">显示原 SVG 对照</button></header><p>原 SVG 约1,300个闭合轮廓。转为原生三角形后共52,276个图片控件，文件约45 MB；数量过多，未达到少图元目标。下图来自实际导出GIA回读后的模拟器运行，未用原图替代角色显示。真机未验证。</p><img id="original" src="/original.svg" alt="原18色SVG"><img src="/screen.png" alt="实际GIA回读模拟器显示"></html>`;
createServer((req,res)=>{
 const paths={'/screen.png':[out+'/actual-gia-simulator.png','image/png'],
 '/study.gia':[out+'/草神_18色矢量几何实验.gia','application/octet-stream'],
 '/original.svg':['outputs/nahida-hd-vector-fit-20261014/hd-fit-18color.svg','image/svg+xml'],
 '/state':[out+'/verification.json','application/json']};
 if(req.url==='/'){res.writeHead(200,{'content-type':'text/html;charset=utf-8'});res.end(html);return;}
 const entry=paths[req.url];if(!entry){res.writeHead(404);res.end();return;}
 res.writeHead(200,{'content-type':entry[1],'cache-control':'no-store'});fs.createReadStream(entry[0]).pipe(res);
}).listen(8821,'127.0.0.1',()=>console.log('http://127.0.0.1:8821/'));
